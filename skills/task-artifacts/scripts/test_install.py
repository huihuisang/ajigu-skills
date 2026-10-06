"""Check installation and relocation with isolated home directories."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SKILL = Path(__file__).resolve().parent.parent


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="task-artifacts-install-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.home = self.base / "original-user"
        self.codex = self.home / ".codex"
        shutil.copytree(SKILL, self.codex / "skills" / "task-artifacts")
        self.environment = dict(os.environ, HOME=str(self.home),
                                GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
        self.environment.pop("CODEX_HOME", None)
        self.environment.pop("CLAUDE_CONFIG_DIR", None)
        self.environment.pop("TASK_ARTIFACT_SKILL_DIR", None)
        self.environment.pop("TASK_ARTIFACT_HOME", None)

    def install(self, ok=True):
        script = self.codex / "skills/task-artifacts/scripts/install.py"
        result = subprocess.run([sys.executable, str(script)], env=self.environment, cwd=self.base,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, ok, result.stderr)
        return result

    def test_reinstall_and_relocate_home(self):
        self.install()
        self.install()
        target_home = self.base / "different-user"
        self.home.rename(target_home)
        self.environment["HOME"] = str(target_home)
        entry = target_home / ".local/bin/task-artifacts"
        self.assertFalse(entry.is_symlink())
        self.assertNotIn(str(self.home), entry.read_text())
        result = subprocess.run([str(entry), "--help"], env=self.environment,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("start,run,verify,finish", result.stdout)
        repository = target_home / "project"
        subprocess.run(["git", "init", str(repository)], env=self.environment,
                       capture_output=True, check=True)
        result = subprocess.run([str(entry), "start", "--repo", str(repository), "--label", "moved home"],
                                env=self.environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads(result.stdout)
        self.assertEqual(Path(state["repository"]), repository)
        self.assertTrue(Path(state["directory"]).is_relative_to(target_home))
        self.assertFalse(self.home.exists())

    def test_custom_codex_home(self):
        custom = self.base / "custom config with spaces"
        self.codex.rename(custom)
        self.codex = custom
        self.environment["CODEX_HOME"] = str(custom)
        self.install()
        entry = self.home / ".local/bin/task-artifacts"
        result = subprocess.run([str(entry), "--help"], env=self.environment,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unrelated_existing_command_is_preserved(self):
        entry = self.home / ".local/bin/task-artifacts"
        entry.parent.mkdir(parents=True)
        entry.write_text("unrelated command\n")
        self.install(ok=False)
        self.assertEqual(entry.read_text(), "unrelated command\n")

    def test_legacy_absolute_symlink_is_replaced(self):
        entry = self.home / ".local/bin/task-artifacts"
        entry.parent.mkdir(parents=True)
        entry.symlink_to(self.codex / "skills/task-artifacts/scripts/task_artifacts.py")
        self.install()
        self.assertFalse(entry.is_symlink())
        self.assertIn("${TASK_ARTIFACT_SKILL_DIR:-$HOME/.agents/skills/task-artifacts}", entry.read_text())

    def test_both_agents_use_one_shared_copy(self):
        self.install()
        shared = self.home / ".agents/skills/task-artifacts"
        for agent_root in (self.home / ".codex", self.home / ".claude"):
            link = agent_root / "skills/task-artifacts"
            self.assertTrue(link.is_symlink())
            self.assertFalse(Path(os.readlink(link)).is_absolute())
            self.assertEqual(link.resolve(), shared)
        self.assertFalse(shared.is_symlink())

    def test_claude_can_run_without_codex_files(self):
        self.install()
        shutil.rmtree(self.codex)
        entry = self.home / ".local/bin/task-artifacts"
        result = subprocess.run([str(entry), "--help"], env=self.environment,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.home / ".claude/skills/task-artifacts/SKILL.md").is_file())

    def test_custom_claude_config_and_shared_location(self):
        config = self.home / "Claude config with spaces"
        shared = self.home / "shared skills with spaces/task-artifacts"
        self.environment["CLAUDE_CONFIG_DIR"] = str(config)
        self.environment["TASK_ARTIFACT_SKILL_DIR"] = str(shared)
        self.install()
        self.assertEqual((config / "skills/task-artifacts").resolve(), shared)
        entry = self.home / ".local/bin/task-artifacts"
        result = subprocess.run([str(entry), "--help"], env=self.environment,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unrelated_claude_skill_is_preserved(self):
        other = self.home / ".claude/skills/task-artifacts"
        other.mkdir(parents=True)
        (other / "keep.txt").write_text("keep")
        self.install(ok=False)
        self.assertEqual((other / "keep.txt").read_text(), "keep")
        self.assertFalse((self.home / ".agents/skills/task-artifacts").exists())
        self.assertFalse((self.home / ".local/bin/task-artifacts").exists())

    def test_symlinked_agent_home_uses_one_shared_copy(self):
        physical = self.home / "physical-config"
        self.codex.rename(physical)
        self.codex.symlink_to(physical, target_is_directory=True)
        self.install()
        shared = self.home / ".agents/skills/task-artifacts"
        self.assertTrue((physical / "skills/task-artifacts").is_symlink())
        self.assertEqual((physical / "skills/task-artifacts").resolve(), shared)
        self.assertEqual((self.home / ".claude/skills/task-artifacts").resolve(), shared)
        self.assertEqual(len(list(self.home.rglob("task_artifacts.py"))), 1)

    def test_nonabsolute_shared_overrides_are_rejected(self):
        for override in ("~/custom-skills/task-artifacts", "relative-skills/task-artifacts"):
            with self.subTest(override=override):
                self.environment["TASK_ARTIFACT_SKILL_DIR"] = override
                self.assertIn("absolute", self.install(ok=False).stderr)
                self.assertFalse((self.home / ".agents/skills/task-artifacts").exists())
                self.assertFalse((self.home / ".local/bin/task-artifacts").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
