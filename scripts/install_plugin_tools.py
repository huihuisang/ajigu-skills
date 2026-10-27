"""Install an optional launcher backed by the selected plugin, without skill copies."""

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile


MARKER = '# ajigu-skills plugin launcher'
LEGACY_MARKER = '# task-artifacts portable launcher'
REPOSITORY = 'https://github.com/huihuisang/ajigu-skills'
LAUNCHER = '''#!/bin/sh
# ajigu-skills plugin launcher
set -eu
task_skill_dir="${TASK_ARTIFACT_SKILL_DIR:-$HOME/.local/share/ajigu-skills/current/skills/task-artifacts}"
case "$task_skill_dir" in
    /*) ;;
    *)
        printf '%s\\n' 'Refused: TASK_ARTIFACT_SKILL_DIR must be absolute.' >&2
        exit 1
        ;;
esac
exec python3 "$task_skill_dir/scripts/task_artifacts.py" "$@"
'''


def is_package(root):
    try:
        data = json.loads((root / 'plugin.json').read_text(encoding='utf-8'))
        return isinstance(data, dict) and data.get('name') == 'ajigu-skills' and data.get('repository') == REPOSITORY
    except (OSError, ValueError):
        return False


def install(source, home):
    if os.name != 'posix':
        raise ValueError('Plugin tool initialization requires a POSIX system.')
    import fcntl
    source = source.resolve()
    home = home.resolve()
    alias = home / '.local/share/ajigu-skills/current'
    destination = home / '.local/bin/task-artifacts'
    if not is_package(source) or not (source / 'skills/task-artifacts/scripts/task_artifacts.py').is_file():
        raise ValueError('Run this initializer from a complete Ajigu Skills plugin.')
    if alias.is_relative_to(source):
        raise ValueError('The stable link cannot be created inside the plugin source.')
    alias.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (alias.parent / '.install.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        header = []
        if destination.is_symlink():
            raise ValueError('Refused: an unrelated command link already exists.')
        if destination.exists():
            if not destination.is_file():
                raise ValueError('Refused: an unrelated command path already exists.')
            header = destination.read_text(encoding='utf-8', errors='replace').splitlines()[:3]
            if not any(marker in header for marker in (MARKER, LEGACY_MARKER)):
                raise ValueError('Refused: an unrelated command already exists.')
        if alias.is_symlink():
            owned_missing_target = not alias.exists() and MARKER in header
            if not is_package(alias.resolve()) and not owned_missing_target:
                raise ValueError('Refused: an unrelated plugin link already exists.')
        elif alias.exists():
            raise ValueError('Refused: a directory or file already occupies the stable link.')
        destination.parent.mkdir(parents=True, exist_ok=True)
        old_link = os.readlink(alias) if alias.is_symlink() else None
        relative = os.path.relpath(source, alias.parent.resolve())
        with tempfile.TemporaryDirectory(dir=alias.parent, prefix='.plugin-link-') as staging:
            staged_link = Path(staging) / 'current'
            staged_link.symlink_to(relative, target_is_directory=True)
            with tempfile.NamedTemporaryFile(dir=destination.parent, prefix='.task-artifacts-', delete=False) as file:
                staged_command = Path(file.name)
                try:
                    file.write(LAUNCHER.encode('utf-8'))
                    file.flush()
                    os.chmod(staged_command, 0o755)
                    os.replace(staged_link, alias)
                    try:
                        os.replace(staged_command, destination)
                    except OSError:
                        if old_link is None:
                            alias.unlink()
                        else:
                            staged_link.symlink_to(old_link, target_is_directory=True)
                            os.replace(staged_link, alias)
                        raise
                finally:
                    staged_command.unlink(missing_ok=True)
    return {'plugin': str(source), 'stable_root': str(alias), 'launcher': str(destination),
            'skill_copies_created': 0, 'standalone_entries_removed': 0}


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    if sys.version_info < (3, 10) or os.name != 'posix':
        raise SystemExit('Python 3.10+ and a POSIX system are required.')
    try:
        print(json.dumps(install(Path(__file__).resolve().parents[1], Path.home()), indent=2))
    except (OSError, ValueError) as error:
        raise SystemExit(f'Initialization refused: {error}') from None
