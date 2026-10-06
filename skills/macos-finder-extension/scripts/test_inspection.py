"""Check Finder inspection failures with local bundle fixtures and command stubs."""

import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("inspect_finder_extension.sh")


@unittest.skipUnless(sys.platform == "darwin", "Requires macOS PlistBuddy and plutil")
class InspectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="finder-inspection-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.app = self.root / "Example App.app"
        self.relative = "Contents/PlugIns/FinderExtension.appex"
        self.extension = self.app / self.relative
        self.write_info(self.app, {"CFBundleIdentifier": "com.example.App"})
        self.extension_info = {
            "NSExtension": {
                "NSExtensionPointIdentifier": "com.apple.FinderSync",
                "NSExtensionPrincipalClass": "Example.FinderSync",
            }
        }
        self.write_info(self.extension, self.extension_info)
        commands = self.root / "bin"
        commands.mkdir()
        codesign = commands / "codesign"
        codesign.write_text(
            '#!/bin/bash\n'
            'case "$1" in\n'
            '  --verify) exit "${TEST_SIGNATURE_EXIT:-0}" ;;\n'
            'esac\n'
            'if [[ "$*" == *"--entitlements"* ]]; then\n'
            '  [[ "${TEST_ENTITLEMENTS_EXIT:-0}" == 0 ]] || exit 1\n'
            '  printf "<plist version=\\"1.0\\"><dict/></plist>\\n"\n'
            'elif [[ "$*" == *".appex"* ]]; then\n'
            '  printf "TeamIdentifier=%s\\n" "${TEST_EXTENSION_TEAM:-EXAMPLE123}" >&2\n'
            'else\n'
            '  printf "TeamIdentifier=EXAMPLE123\\n" >&2\n'
            'fi\n', encoding="utf-8"
        )
        codesign.chmod(0o755)
        pluginkit = commands / "pluginkit"
        pluginkit.write_text(
            '#!/bin/bash\n'
            'for ((i=0; i<${TEST_REGISTRATIONS:-1}; i++)); do\n'
            '  printf "com.example.App.FinderExtension /Applications/Example.app\\n"\n'
            'done\n', encoding="utf-8"
        )
        pluginkit.chmod(0o755)
        self.environment = dict(os.environ, PATH=str(commands) + os.pathsep + os.environ["PATH"])

    def write_info(self, bundle, data):
        info = bundle / "Contents/Info.plist"
        info.parent.mkdir(parents=True, exist_ok=True)
        info.write_bytes(plistlib.dumps(data))

    def inspect(self, *extra, relative=None):
        return subprocess.run(
            ["bash", str(SCRIPT), str(self.app), relative or self.relative, *extra],
            env=self.environment, text=True, capture_output=True,
        )

    def test_valid_structure_and_registration(self):
        result = self.inspect("com.example.App.FinderExtension")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS:", result.stdout)

    def test_wrong_extension_point(self):
        self.extension_info["NSExtension"]["NSExtensionPointIdentifier"] = "com.example.Other"
        self.write_info(self.extension, self.extension_info)
        result = self.inspect()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not a Finder Sync", result.stderr)

    def test_missing_principal_class(self):
        del self.extension_info["NSExtension"]["NSExtensionPrincipalClass"]
        self.write_info(self.extension, self.extension_info)
        result = self.inspect()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("lacks its principal class", result.stderr)

    def test_invalid_signature(self):
        self.environment["TEST_SIGNATURE_EXIT"] = "1"
        result = self.inspect()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("PASS:", result.stdout)

    def test_unreadable_entitlements(self):
        self.environment["TEST_ENTITLEMENTS_EXIT"] = "1"
        result = self.inspect()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("could not read", result.stderr)

    def test_mismatched_teams(self):
        self.environment["TEST_EXTENSION_TEAM"] = "DIFFERENT1"
        result = self.inspect()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("different signing teams", result.stderr)

    def test_duplicate_registration(self):
        self.environment["TEST_REGISTRATIONS"] = "2"
        result = self.inspect("com.example.App.FinderExtension")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("found 2", result.stderr)

    def test_path_outside_app(self):
        result = self.inspect(relative="../Outside.appex")
        self.assertEqual(result.returncode, 64)
        self.assertIn("must stay relative", result.stderr)


if __name__ == "__main__":
    unittest.main()
