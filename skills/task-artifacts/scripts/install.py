#!/usr/bin/env python3
"""Install one shared skill with Codex and Claude Code discovery links."""

import argparse
import os
from pathlib import Path
import shutil
import tempfile
import sys

if sys.version_info < (3, 10):
    raise SystemExit("Python 3.10 or later is required.")
if os.name != "posix":
    raise SystemExit("The installer requires a POSIX system with symbolic links.")


MARKER = "# task-artifacts portable launcher"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bin-dir", type=Path, default=Path.home() / ".local" / "bin")
    args = parser.parse_args()
    source_root = Path(__file__).resolve().parent.parent
    shared_setting = Path(os.environ.get("TASK_ARTIFACT_SKILL_DIR", str(Path.home() / ".agents/skills/task-artifacts")))
    if not shared_setting.is_absolute():
        parser.exit(1, "Refused: TASK_ARTIFACT_SKILL_DIR must be absolute. Set it with $HOME.\n")
    if shared_setting.is_symlink():
        parser.exit(1, "Refused: The shared skill cannot itself be a symbolic link.\n")
    shared = shared_setting.resolve()
    agent_roots = [Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser().resolve(),
                   Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude"))).expanduser().resolve()]
    links = list(dict.fromkeys(root / "skills/task-artifacts" for root in agent_roots))
    destination_dir = args.bin_dir.expanduser().resolve()
    destination = destination_dir / "task-artifacts"

    # Reject conflicts before changing any skill or command path.
    if shared.is_symlink() or (shared.exists() and shared.resolve() != source_root):
        parser.exit(1, "Refused: A different shared skill already exists.\n")
    if shared != source_root and shared.is_relative_to(source_root):
        parser.exit(1, "Refused: Shared skill cannot be installed inside its source.\n")
    for link in links:
        if link == shared:
            continue
        if link.exists() or link.is_symlink():
            if link.resolve() not in (source_root, shared):
                parser.exit(1, "Refused: An unrelated agent skill already exists.\n")
    if destination.is_symlink():
        if destination.resolve() not in (source_root / "scripts/task_artifacts.py", shared / "scripts/task_artifacts.py"):
            parser.exit(1, "Refused: An unrelated command link already exists.\n")
    elif destination.exists():
        if not destination.is_file() or MARKER not in destination.read_text(encoding="utf-8", errors="replace").splitlines()[:3]:
            parser.exit(1, "Refused: An unrelated command already exists.\n")

    if not shared.exists():
        shared.parent.mkdir(parents=True, exist_ok=True)
        if source_root in links:
            # Move only the skill used to invoke this installer, never another installed copy.
            source_root.rename(shared)
        else:
            shutil.copytree(source_root, shared)
    for link in links:
        if link == shared:
            continue
        relative_target = os.path.relpath(shared, link.parent)
        if link.is_symlink() and os.readlink(link) == relative_target:
            continue
        link.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=link.parent, prefix=".task-artifacts-link-") as staging:
            temporary_link = Path(staging) / "skill"
            temporary_link.symlink_to(relative_target, target_is_directory=True)
            os.replace(temporary_link, link)

    launcher = shared / "scripts/task-artifacts"
    destination_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination_dir, prefix=".task-artifacts-", delete=False) as output:
        temporary = Path(output.name)
        try:
            output.write(launcher.read_bytes())
            output.flush()
            os.chmod(temporary, 0o755)
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
    print(f"Installed: {destination}")
    print(f"Shared skill: {shared}")
    print("Codex and Claude Code use the same skill through relative discovery links.")
    print("The launcher resolves TASK_ARTIFACT_SKILL_DIR or ~/.agents/skills/task-artifacts.")


if __name__ == "__main__":
    main()
