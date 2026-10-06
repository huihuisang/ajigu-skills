import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "icon_tools.py"


class IconToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.brief = {
            "subject": "a folded paper moon", "material": "soft paper",
            "palette": ["#223344", "#FFEEDD"],
            "details": ["one curved fold", "one small star"],
        }

    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              capture_output=True, text=True)

    def compose(self, brief):
        source = self.directory / "brief.json"
        source.write_text(json.dumps(brief), encoding="utf-8")
        return self.run_tool("prompt", source, "--out", self.directory / "prompt.txt")

    def test_square_default_and_saved_prompt(self):
        result = self.compose(self.brief)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        prompt = (self.directory / "prompt.txt").read_text(encoding="utf-8")
        self.assertIn("four sharp 90-degree corners", prompt)
        self.assertIn("The square artwork itself IS a folded paper moon", prompt)
        self.assertIn("#223344", prompt)
        self.assertNotIn("80%", prompt)

    def test_foreground_does_not_request_opaque_background(self):
        self.brief["mode"] = "foreground"
        result = self.compose(self.brief)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        prompt = (self.directory / "prompt.txt").read_text(encoding="utf-8")
        self.assertIn("transparent background", prompt)
        self.assertNotIn("opaque background", prompt)
        self.assertNotIn("toylike", prompt)

    def test_bad_briefs_fail_without_output(self):
        for key, value in [("palette", ["blue"]), ("details", ["one"]),
                           ("mode", "rounded"), ("subject", ""),
                           ("unknown", True), ("details", "not a list")]:
            with self.subTest(key=key, value=value):
                brief = copy.deepcopy(self.brief)
                brief[key] = value
                self.assertNotEqual(self.compose(brief).returncode, 0)
                self.assertFalse((self.directory / "prompt.txt").exists())

    def test_existing_prompt_is_preserved(self):
        destination = self.directory / "prompt.txt"
        destination.write_text("User work", encoding="utf-8")
        self.assertNotEqual(self.compose(self.brief).returncode, 0)
        self.assertEqual(destination.read_text(), "User work")

    def test_invalid_json_has_clear_error(self):
        source = self.directory / "brief.json"
        source.write_text("{", encoding="utf-8")
        result = self.run_tool("prompt", source, "--out", self.directory / "prompt.txt")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["status"], "error")

    @unittest.skipUnless(importlib.util.find_spec("PIL"), "Pillow is not available")
    def test_image_contracts_and_corrupt_files(self):
        from PIL import Image
        path = self.directory / "source.png"
        image = Image.new("RGBA", (1024, 1024), (40, 60, 80, 255))
        image.save(path)
        result = self.run_tool("check", path)
        self.assertEqual(result.returncode, 0, result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["visual_review"], "pending")
        self.assertNotEqual(self.run_tool("check", path, "--mode", "foreground").returncode, 0)
        image.putpixel((0, 0), (0, 0, 0, 0))
        image.save(path)
        self.assertNotEqual(self.run_tool("check", path).returncode, 0)
        self.assertEqual(self.run_tool("check", path, "--mode", "foreground").returncode, 0)
        Image.new("RGBA", (1024, 1024), (0, 0, 0, 0)).save(path)
        self.assertNotEqual(self.run_tool("check", path, "--mode", "foreground").returncode, 0)
        Image.new("RGB", (512, 1024)).save(path)
        self.assertNotEqual(self.run_tool("check", path).returncode, 0)
        path.write_bytes(b"not an image")
        self.assertNotEqual(self.run_tool("check", path).returncode, 0)


if __name__ == "__main__":
    unittest.main()
