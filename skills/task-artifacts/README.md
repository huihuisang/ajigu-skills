# Task Artifacts

Track disposable task outputs and remove only the registered directory after source verification and publication checks pass. Failed validation, changed sources, active processes, or an unconfirmed remote branch preserve the outputs. The command does not commit or push.

## Install

Ask your Agent: "Install task-artifacts from https://github.com/huihuisang/ajigu-skills."

```bash
npx skills add huihuisang/ajigu-skills -g -y --skill task-artifacts
```

Command installation needs Node.js and network access; the runtime does not. For a plugin-only installation, run `python3 scripts/install_plugin_tools.py` from the installed Ajigu Skills plugin root. This optional initializer creates a stable plugin-root link and the command without copying skills or creating standalone discovery entries. Rerun it from the new plugin root after each upgrade. It preserves existing standalone skills; retire them separately after comparing changes and repairing old instruction paths.

For a standalone installation, the package includes optional Codex and Claude Code discovery integration. Run the following installer from the installed skill directory:

```bash
python3 scripts/install.py
```

The installer creates a shared copy under `~/.agents/skills/task-artifacts`, relative discovery links, and a launcher in `~/.local/bin`. It refuses unrelated existing skills and commands. It does not edit global instructions, hooks, or shell configuration. Add the launcher directory to PATH using your normal shell configuration.

## Configuration and requirements

Requires Python 3.10+, Git, a POSIX filesystem with flock, and lsof. macOS is tested; Linux is not verified and Windows is unsupported. Git repositories and colocated jj repositories are supported. No API key or service account is needed.

Use `TASK_ARTIFACT_SKILL_DIR` for a custom absolute shared installation path. `CODEX_HOME` and `CLAUDE_CONFIG_DIR` customize optional agent discovery locations. See [SKILL.md](SKILL.md) for the command contract and migration limits.

## Usage and output

```bash
task-artifacts start --repo /absolute/project --label feature-work
```

The result supplies a task ID and an isolated output directory. Run output-producing commands through `run`, real checks through `verify`, then use `finish` to preview eligibility. `finish --apply` removes the directory only after its guards pass. Retain required evidence and deliverables outside that directory. Global instructions can reference this workflow, but installation alone does not enforce it for other agents or manual commands.

## Security and privacy

State and receipts stay in the user's local data directory. The finish check contacts the configured Git push destination with ls-remote and the user's normal Git authentication; the tool does not collect credentials. Installing the tool does not grant permission to delete task outputs. Obtain authorization for that scope and preserve project files, historical outputs, shared caches, and user data.

Do not copy active task state between computers or edit its absolute paths to resume it. Start a new task on the new computer and rerun the required checks. Cleanup checks open files but cannot predict future activity from unmanaged background processes.

## Validation and troubleshooting

```bash
python3 scripts/test_task_artifacts.py
python3 scripts/test_install.py
```

The tests use disposable local repositories and isolated fake home directories; they do not contact production remotes. Keep failed outputs when a guard refuses cleanup, correct the cause, and rerun verification if sources changed. Do not weaken guards to make cleanup pass.
