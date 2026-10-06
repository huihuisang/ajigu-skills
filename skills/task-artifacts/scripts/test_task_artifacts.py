"""Exercise cleanup boundaries against disposable local repositories."""

from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("task_artifacts.py")


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="task-artifacts-tests-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.repo = self.base / "repository"
        self.repo.mkdir()
        self.home = self.base / "artifacts"
        self.environment = dict(os.environ, TASK_ARTIFACT_HOME=str(self.home),
                                GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
                                GIT_TERMINAL_PROMPT="0")
        self.shell(["git", "init", "--initial-branch=master", str(self.repo)])
        self.shell(["git", "init", "--bare", str(self.base / "remote.git")])
        self.git("config", "user.name", "Artifact Test")
        self.git("config", "user.email", "artifact-test@example.invalid")
        self.git("config", "core.hooksPath", str(self.base / "no-hooks"))
        self.git("remote", "add", "origin", str(self.base / "remote.git"))
        (self.repo / "source.txt").write_text("version one\n")
        self.commit()
        self.state = json.loads(self.cli("start", "--repo", str(self.repo), "--label", "test").stdout)
        self.task_id = self.state["id"]
        self.root = Path(self.state["directory"])
        (self.root / "output.bin").write_bytes(b"disposable")

    def shell(self, args):
        return subprocess.run(args, cwd=self.repo, env=self.environment, capture_output=True,
                              text=True, check=True).stdout.strip()

    def git(self, *args):
        return self.shell(["git", *args])

    def commit(self):
        self.git("add", "--all")
        self.git("commit", "-m", "Update test source")
        return self.git("rev-parse", "HEAD")

    def cli(self, *args, ok=True):
        result = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.repo,
                                env=self.environment, capture_output=True, text=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def verify(self, program="pass", source="source.txt", ok=True):
        return self.cli("verify", self.task_id, "--source", source, "--",
                        sys.executable, "-c", program, ok=ok)

    def publish(self):
        self.git("push", "origin", "master")

    def finish(self, apply=True, ok=True, revision="HEAD"):
        args = ["finish", self.task_id, "--revision", revision, "--branch", "master"]
        if apply:
            args.append("--apply")
        return self.cli(*args, ok=ok)

    def test_unverified_task_is_preserved(self):
        self.publish()
        self.assertIn("no successful verification", self.finish(ok=False).stderr)
        self.assertTrue(self.root.exists())

    def test_failed_check_invalidates_previous_verification(self):
        self.verify()
        self.verify("raise SystemExit(7)", ok=False)
        self.publish()
        self.finish(ok=False)
        self.assertTrue(self.root.exists())

    def test_unpublished_commit_is_preserved(self):
        self.verify()
        self.finish(ok=False)
        self.assertTrue(self.root.exists())

    def test_failed_remote_check_preserves_outputs(self):
        self.verify()
        self.git("remote", "set-url", "origin", str(self.base / "missing.git"))
        self.finish(ok=False)
        self.assertTrue(self.root.exists())

    def test_publication_uses_push_destination(self):
        self.verify()
        self.publish()
        destination = self.base / "push.git"
        self.shell(["git", "init", "--bare", str(destination)])
        self.git("remote", "set-url", "--push", "origin", str(destination))
        self.finish(ok=False)
        self.assertTrue(self.root.exists())
        self.publish()
        self.finish()
        self.assertFalse(self.root.exists())

    def test_multiple_push_destinations_preserve_outputs(self):
        self.verify()
        self.publish()
        destination = self.base / "second.git"
        self.shell(["git", "init", "--bare", str(destination)])
        self.git("remote", "set-url", "--add", "--push", "origin", str(self.base / "remote.git"))
        self.git("remote", "set-url", "--add", "--push", "origin", str(destination))
        self.assertIn("one push destination", self.finish(ok=False).stderr)
        self.assertTrue(self.root.exists())

    def test_changed_verified_source_is_preserved(self):
        self.verify()
        self.publish()
        (self.repo / "source.txt").write_text("version two\n")
        self.assertIn("sources changed", self.finish(ok=False).stderr)
        self.assertTrue(self.root.exists())

    def test_source_change_during_check_cannot_be_attested(self):
        self.verify("from pathlib import Path; Path('source.txt').write_text('changed')", ok=False)
        self.publish()
        self.finish(ok=False)
        self.assertTrue(self.root.exists())

    def test_verified_but_uncommitted_source_is_preserved(self):
        (self.repo / "source.txt").write_text("version two\n")
        self.verify()
        self.publish()
        self.assertIn("commit does not contain", self.finish(ok=False).stderr)
        self.assertTrue(self.root.exists())

    def test_preview_keeps_outputs(self):
        self.verify()
        self.publish()
        report = json.loads(self.finish(apply=False).stdout)
        self.assertTrue(report["eligible"])
        self.assertFalse(report["cleaned"])
        self.assertTrue(self.root.exists())

    def test_cleanup_only_removes_its_own_directory(self):
        other = json.loads(self.cli("start", "--label", "other task").stdout)
        outside = self.base / "keep.txt"
        outside.write_text("keep")
        (self.root / "external-link").symlink_to(outside)
        legacy = self.repo / "build"
        legacy.mkdir()
        (legacy / "keep.bin").write_bytes(b"keep")
        self.verify()
        self.publish()
        self.finish()
        self.assertFalse(self.root.exists())
        self.assertTrue(Path(other["directory"]).exists())
        self.assertEqual(outside.read_text(), "keep")
        self.assertEqual((legacy / "keep.bin").read_bytes(), b"keep")
        receipt = json.loads((self.home / "state" / (self.task_id + ".json")).read_text())
        self.assertEqual(receipt["status"], "cleaned")

    def test_redirected_task_root_is_preserved(self):
        self.verify()
        self.publish()
        old = self.root.with_name(self.root.name + "-moved")
        self.root.rename(old)
        self.root.symlink_to(old, target_is_directory=True)
        self.assertIn("redirected", self.finish(ok=False).stderr)
        self.assertTrue((old / "output.bin").exists())

    def test_task_lock_prevents_cleanup(self):
        self.verify()
        self.publish()
        with (self.home / "state" / (self.task_id + ".lock")).open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertIn("Task is active", self.finish(ok=False).stderr)
        self.assertTrue(self.root.exists())

    def test_open_output_prevents_cleanup(self):
        self.verify()
        self.publish()
        with (self.root / "output.bin").open("rb"):
            self.assertIn("process is using", self.finish(ok=False).stderr)
        self.assertTrue(self.root.exists())

    def test_run_invalidates_previous_verification_and_sets_directory(self):
        self.verify()
        self.cli("run", self.task_id, "--", sys.executable, "-c",
                 "import os; from pathlib import Path; Path(os.environ['TASK_ARTIFACT_DIR'], 'new.txt').write_text('new')")
        self.assertTrue((self.root / "new.txt").exists())
        self.publish()
        self.finish(ok=False)

    def test_other_task_source_changes_do_not_block_cleanup(self):
        self.verify()
        self.publish()
        (self.repo / "other.txt").write_text("another task")
        self.finish()
        self.assertEqual((self.repo / "other.txt").read_text(), "another task")

    def test_untracked_task_source_requires_commit(self):
        (self.repo / "new.txt").write_text("new")
        self.verify(source="new.txt")
        self.publish()
        self.finish(ok=False)
        self.commit()
        self.publish()
        self.finish()

    def test_deleted_source_can_be_verified_and_cleaned(self):
        (self.repo / "source.txt").unlink()
        self.verify()
        self.commit()
        self.publish()
        self.finish()
        self.assertFalse(self.root.exists())

    def test_source_escape_is_rejected(self):
        self.assertIn("relative", self.verify(source="../outside", ok=False).stderr)

    def test_copied_task_records_cannot_adopt_a_new_data_directory(self):
        self.verify()
        self.publish()
        migrated = self.base / "new-user-artifacts"
        shutil.copytree(self.home, migrated)
        self.environment["TASK_ARTIFACT_HOME"] = str(migrated)
        self.assertIn("does not match its registration", self.finish(ok=False).stderr)
        self.assertTrue(self.root.exists())
        self.assertTrue((migrated / "work" / self.task_id / "output.bin").exists())

    def test_new_remote_revision_requires_exact_match(self):
        self.verify()
        old = self.git("rev-parse", "HEAD")
        (self.repo / "other.txt").write_text("new revision")
        self.commit()
        self.publish()
        self.assertIn("remote branch does not point", self.finish(revision=old, ok=False).stderr)
        self.assertTrue(self.root.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
