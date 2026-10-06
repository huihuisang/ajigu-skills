#!/usr/bin/env python3
"""Manage task-owned outputs without adopting existing project directories."""

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

if sys.version_info < (3, 10):
    raise SystemExit("Python 3.10 or later is required.")
if os.name != "posix":
    raise SystemExit("Task Artifacts requires a POSIX system with flock and lsof.")

import fcntl


class Refusal(Exception):
    pass


HOME = Path(os.environ.get("TASK_ARTIFACT_HOME", "~/.local/share/task-artifacts")).expanduser().resolve()


def command(args, cwd=None):
    result = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise Refusal(result.stderr.decode(errors="replace").strip() or f"Command failed: {args[0]}")
    return result.stdout


def git(repo, *args):
    return command(["git", "--literal-pathspecs", "-C", str(repo), *args])


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def save(state):
    destination = HOME / "state" / (state["id"] + ".json")
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    temporary.replace(destination)


@contextmanager
def task(task_id):
    if len(task_id) != 32 or any(c not in "0123456789abcdef" for c in task_id):
        raise Refusal("Invalid task ID.")
    manifest = HOME / "state" / (task_id + ".json")
    if not manifest.is_file() or manifest.is_symlink():
        raise Refusal("Task is not registered.")
    with (HOME / "state" / (task_id + ".lock")).open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Refusal("Task is active. Its outputs were preserved.") from None
        state = json.loads(manifest.read_text(encoding="utf-8"))
        root = HOME / "work" / task_id
        if state.get("id") != task_id or state.get("directory") != str(root):
            raise Refusal("Task directory does not match its registration.")
        if root.is_symlink() or root.resolve() != root or root.parent.is_symlink():
            raise Refusal("Task directory contains a redirected path.")
        if state.get("status") == "cleaned":
            raise Refusal("Task was already cleaned. Its receipt is in the state directory.")
        if not root.is_dir():
            raise Refusal("Task directory is missing.")
        yield state, root


def start(args):
    repo = Path(git(Path(args.repo).resolve(), "rev-parse", "--show-toplevel").decode().strip()).resolve()
    for name in ("state", "work"):
        (HOME / name).mkdir(parents=True, exist_ok=True, mode=0o700)
    task_id = uuid.uuid4().hex
    root = HOME / "work" / task_id
    root.mkdir(mode=0o700)
    state = {"id": task_id, "label": args.label, "repository": str(repo),
             "directory": str(root), "created_at": time.time(), "status": "open"}
    save(state)
    emit(state)


def sources(repo, values):
    result = []
    for value in values:
        relative = Path(value)
        if relative.is_absolute() or ".." in relative.parts or not value:
            raise Refusal("Sources must be literal paths relative to the repository.")
        parent = (repo / relative).parent.resolve()
        if relative != Path(".") and not parent.is_relative_to(repo):
            raise Refusal("Source path leaves the repository.")
        result.append(str(relative))
    return sorted(set(result))


def working_snapshot(repo, scope):
    algorithm = git(repo, "rev-parse", "--show-object-format").decode().strip()
    names = git(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", *scope)
    result = {}
    for name in sorted(set(names.split(b"\0")) - {b""}):
        relative = os.fsdecode(name)
        source = repo / relative
        if not source.parent.resolve().is_relative_to(repo):
            raise Refusal("Source path leaves the repository.")
        if source.is_symlink():
            content = os.fsencode(os.readlink(source))
            digest = hashlib.new(algorithm, f"blob {len(content)}\0".encode() + content).hexdigest()
            mode = "120000"
        elif source.is_file():
            stat = source.stat()
            digest_state = hashlib.new(algorithm, f"blob {stat.st_size}\0".encode())
            with source.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest_state.update(chunk)
            digest = digest_state.hexdigest()
            mode = "100755" if stat.st_mode & 0o111 else "100644"
        elif source.exists():
            raise Refusal("A source is not a regular file. Verify submodules in their own repository.")
        else:
            continue
        result[relative] = [mode, digest]
    return result


def revision_snapshot(repo, revision, scope):
    output = git(repo, "ls-tree", "-r", "-z", "--full-tree", revision, "--", *scope)
    result = {}
    for entry in output.split(b"\0"):
        if entry:
            metadata, name = entry.split(b"\t", 1)
            mode, kind, digest = metadata.decode().split()
            if kind != "blob":
                raise Refusal("Verify submodules in their own repository.")
            result[os.fsdecode(name)] = [mode, digest]
    return result


def run(args, verify=False):
    if not args.command:
        raise Refusal("Supply a command after --.")
    with task(args.id) as (state, root):
        repo = Path(state["repository"])
        state.pop("verification", None)
        save(state)
        if verify:
            scope = sources(repo, args.source)
            before = working_snapshot(repo, scope)
            if not git(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", *scope):
                raise Refusal("Verification scope has no files. Include an existing task source file.")
        environment = dict(os.environ, TASK_ARTIFACT_DIR=str(root))
        result = subprocess.run(args.command, cwd=repo, env=environment)
        if result.returncode:
            raise Refusal(f"Command exited with {result.returncode}. Outputs were preserved.")
        if verify:
            after = working_snapshot(repo, scope)
            if before != after:
                raise Refusal("Sources changed during verification. Run verification again.")
            state["verification"] = {"sources": scope, "snapshot": after, "checked_at": time.time()}
            save(state)
            emit({"verified": True, "id": args.id, "files": len(after)})


def assert_idle(root):
    # Managed runs hold the task lock. Also catch open files in unmanaged processes.
    result = subprocess.run(["lsof", "-nP", "+D", str(root)], capture_output=True)
    if result.returncode == 0 or result.stdout:
        raise Refusal("A process is using task outputs. They were preserved.")
    if result.returncode != 1 or result.stderr:
        raise Refusal("Could not confirm that task outputs are idle. They were preserved.")


def finish(args):
    with task(args.id) as (state, root):
        repo = Path(state["repository"])
        verified = state.get("verification")
        if not verified:
            raise Refusal("Task has no successful verification. Outputs were preserved.")
        scope = verified["sources"]
        snapshot = verified["snapshot"]
        if working_snapshot(repo, scope) != snapshot:
            raise Refusal("Verified sources changed. Run verification again.")
        revision = git(repo, "rev-parse", "--verify", "--end-of-options", args.revision + "^{commit}").decode().strip()
        if revision_snapshot(repo, revision, scope) != snapshot:
            raise Refusal("The commit does not contain the verified sources. Outputs were preserved.")
        if args.remote not in git(repo, "remote").decode().splitlines():
            raise Refusal("Select a configured remote by name.")
        destinations = git(repo, "remote", "get-url", "--push", "--all", args.remote).decode().splitlines()
        if len(destinations) != 1:
            raise Refusal("Cleanup requires exactly one push destination. Outputs were preserved.")
        branch = "refs/heads/" + args.branch
        git(repo, "check-ref-format", branch)
        published = git(repo, "ls-remote", "--exit-code", "--refs", "--", destinations[0], branch).decode().splitlines()
        if len(published) != 1 or published[0].split("\t") != [revision, branch]:
            raise Refusal("The remote branch does not point to the verified commit. Outputs were preserved.")
        assert_idle(root)
        report = {"id": args.id, "directory": str(root), "revision": revision,
                  "remote": args.remote, "branch": args.branch, "eligible": True, "cleaned": False}
        if args.apply:
            # Recheck after the remote request. Only this registered directory is removable.
            if working_snapshot(repo, scope) != snapshot:
                raise Refusal("Sources changed while checking publication. Outputs were preserved.")
            shutil.rmtree(root)
            state.update(status="cleaned", cleaned_at=time.time(), publication=report)
            state["publication"]["cleaned"] = True
            save(state)
            report["cleaned"] = True
        emit(report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    begin = commands.add_parser("start", help="Create an isolated task output directory.")
    begin.add_argument("--repo", default=".")
    begin.add_argument("--label", required=True)
    begin.set_defaults(handler=start)
    for name in ("run", "verify"):
        execute = commands.add_parser(name)
        execute.add_argument("id")
        if name == "verify":
            execute.add_argument("--source", action="append", required=True)
        execute.set_defaults(handler=lambda args, checking=name == "verify": run(args, checking))
    end = commands.add_parser("finish", help="Check publication; use --apply to remove task outputs.")
    end.add_argument("id")
    end.add_argument("--revision", required=True)
    end.add_argument("--remote", default="origin")
    end.add_argument("--branch", required=True)
    end.add_argument("--apply", action="store_true")
    end.set_defaults(handler=finish)
    raw = sys.argv[1:]
    if "--" in raw:
        separator = raw.index("--")
        args = parser.parse_args(raw[:separator])
        args.command = raw[separator + 1:]
    else:
        args = parser.parse_args(raw)
        args.command = []
    try:
        args.handler(args)
    except (Refusal, OSError, ValueError) as error:
        print(f"Refused: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
