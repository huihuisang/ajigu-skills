"""Exercise the menu image inspector through its actual command entry point."""

import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile
import unittest


@unittest.skipUnless(sys.platform == "darwin" and shutil.which("swiftc"), "Requires macOS and Swift")
class MenuIconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="menu-icon-test-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        cls.bundle = cls.root / "Example.app"
        resources = cls.bundle / "Contents/Resources"
        resources.mkdir(parents=True)
        (cls.bundle / "Contents/Info.plist").write_bytes(plistlib.dumps({
            "CFBundleIdentifier": "com.example.MenuIconTests", "CFBundlePackageType": "APPL",
        }))
        cls.inspector = cls.root / "inspect-menu-icon"
        source = Path(__file__).with_name("inspect_menu_icon.swift")
        subprocess.run(["swiftc", str(source), "-o", str(cls.inspector)], check=True, capture_output=True)
        generator = cls.root / "fixtures.swift"
        generator.write_text('''import AppKit
import CoreGraphics
let root = URL(fileURLWithPath: CommandLine.arguments[1])
for (name, size, red, empty) in [
    ("ActionTemplate", 16.0, 0.0, false), ("Plain", 16.0, 0.0, false),
    ("ColoredTemplate", 16.0, 1.0, false), ("ColorArtwork", 16.0, 1.0, false),
    ("OpaqueArtwork", 16.0, 1.0, false), ("BigTemplate", 64.0, 0.0, false),
    ("EmptyTemplate", 16.0, 0.0, true)
] {
    var box = CGRect(x: 0, y: 0, width: size, height: size)
    let consumer = CGDataConsumer(url: root.appendingPathComponent(name + ".pdf") as CFURL)!
    let context = CGContext(consumer: consumer, mediaBox: &box, nil)!
    context.beginPDFPage(nil)
    if !empty {
        context.setFillColor(red: red, green: 0, blue: 0, alpha: 1)
        context.fill(name == "OpaqueArtwork" ? box : CGRect(x: size / 4, y: size / 4, width: size / 2, height: size / 2))
    }
    context.endPDFPage()
    context.closePDF()
}
''', encoding="utf-8")
        executable = cls.root / "fixtures"
        subprocess.run(["swiftc", str(generator), "-o", str(executable)], check=True, capture_output=True)
        subprocess.run([str(executable), str(resources)], check=True, capture_output=True)


    def inspect(self, name):
        return subprocess.run([str(self.inspector), str(self.bundle), name], text=True, capture_output=True)

    def test_portable_template_and_archive_are_verified(self):
        result = self.inspect("ActionTemplate")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["isTemplate"])
        self.assertTrue(report["resourceDecodable"])
        self.assertTrue(report["archivePreservesRenderingIntent"])
        self.assertFalse(report["finderAppearanceVerified"])
        self.assertGreater(report["visiblePixels"], 0)
        self.assertGreater(report["transparentPixels"], 0)

    def test_non_template_is_rejected(self):
        result = self.inspect("Plain")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not marked as a template", result.stderr)

    def test_colored_template_is_rejected(self):
        result = self.inspect("ColoredTemplate")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("monochrome with transparency", result.stderr)

    def test_missing_resource_is_rejected(self):
        result = self.inspect("MissingTemplate")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing", result.stderr)

    def test_oversized_menu_image_is_rejected(self):
        result = self.inspect("BigTemplate")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("at most 24 points", result.stderr)

    def test_empty_mask_is_rejected(self):
        result = self.inspect("EmptyTemplate")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("visible mask", result.stderr)

    def test_usage_requires_bundle_and_image_name(self):
        result = subprocess.run([str(self.inspector)], text=True, capture_output=True)
        self.assertEqual(result.returncode, 64)
        self.assertIn("Usage:", result.stderr)

    def test_system_template_keeps_its_name_through_archiving(self):
        result = subprocess.run([str(self.inspector), "--system-image", "NSAddTemplate"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["transport"], "system-name")
        self.assertTrue(report["archivePreservesSystemName"])
        self.assertFalse(report["finderAppearanceVerified"])

    def test_non_template_system_image_is_rejected(self):
        result = subprocess.run([str(self.inspector), "--system-image", "NSFolder"], text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not marked as a template", result.stderr)

    def test_artwork_preserves_full_color_intent(self):
        result = subprocess.run([str(self.inspector), str(self.bundle), "ColorArtwork", "--full-color"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["isTemplate"])
        self.assertEqual(report["renderingIntent"], "full-color")
        self.assertTrue(report["archivePreservesRenderingIntent"])
        self.assertGreater(report["coloredPixels"], 0)
        self.assertFalse(report["finderAppearanceVerified"])

    def test_touch_bar_only_artwork_is_not_a_menu_fallback(self):
        result = subprocess.run([str(self.inspector), "--system-image", "NSTouchBarDownloadTemplate"], text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Touch Bar-only", result.stderr)

    def test_opaque_full_color_artwork_does_not_require_a_template_mask(self):
        result = subprocess.run([str(self.inspector), str(self.bundle), "OpaqueArtwork", "--full-color"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["transparentPixels"], 0)


if __name__ == "__main__":
    unittest.main()
