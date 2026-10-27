# Ajigu Skills

A collection of reusable agent skills for app artwork, App Store operations, macOS development and distribution, project decisions, task outputs, disk cleanup, UI research, and equity analysis.

## Skills

| Skill | Purpose | Optional dependencies |
| --- | --- | --- |
| `app-icon-studio` | Generate square app icon artwork, reusable prompts, and optional transparent foreground assets for Icon Composer. | Host image generation; Python 3.10+ for prompts; Pillow for image checks |
| `localize-app-store-screenshots` | Localize text in existing App Store screenshots while preserving product imagery. | Python 3, Pillow, NumPy, OpenCV; `asc`, `asc-shots-pipeline`, and `asc-cli-usage` for upload workflows |
| `mobbin-search` | Search Mobbin for real product screenshots and download results for visual analysis. | Python 3, a Mobbin API key; 1Password CLI for the recommended secret workflow |
| `smooth-alpha-edges` | Repair jagged transparent-image silhouettes while preserving interior pixels. | Bash, ImageMagick |
| `stock-value-analysis` | Analyze long-term equity value with structured history, recent filings, and anomaly-driven research. | Internet access and market-data sources |
| `xcode-cloud-setup` | Audit, configure, and diagnose Xcode Cloud workflows. | `asc`, `jq`, App Store Connect authentication |
| [`write-ai-doc`](skills/write-ai-doc/README.md) | Record project decisions, acceptance criteria, and verified implementation results in docs-ai. | Agent file access; Simplified Chinese by default |
| [`task-artifacts`](skills/task-artifacts/README.md) | Track task outputs and gate cleanup on verification, publication, and idle checks. | Python 3.10+, Git, lsof; macOS tested; optional agent integration |
| [`macos-direct-distribution`](skills/macos-direct-distribution/README.md) | Prepare Developer ID signing, notarization, stapling, and DMG release evidence. | macOS, Xcode tools; authorized Apple signing and notarization access |
| [`macos-finder-extension`](skills/macos-finder-extension/README.md) | Build and diagnose Finder Sync extensions, signing, permissions, and registration. | macOS system tools; Xcode for builds |
| [`disk-cleanup`](skills/disk-cleanup/README.md) | Inspect development storage and clean only authorized, verified candidates. | macOS terminal; relevant development tools when installed |

## Install

Choose the complete plugin for one versioned bundle, or install individual skills with the Skills CLI. Both options use the same `skills/` sources. Plugins contain all 11 skills and have no hooks or MCP servers.

### Codex plugin

```bash
codex plugin marketplace add huihuisang/ajigu-skills
codex plugin add ajigu-skills@ajigu-skills
```

The repository marketplace is named `ajigu-skills`. Restart the host or start a new session after installation if it has already loaded its skill inventory. This is a repository-distributed plugin; it is not a listing in the official public plugin directory.

### Claude Code plugin

```bash
claude plugin marketplace add huihuisang/ajigu-skills
claude plugin install ajigu-skills@ajigu-skills
```

The same steps are available as `/plugin marketplace add huihuisang/ajigu-skills` and `/plugin install ajigu-skills@ajigu-skills` inside Claude Code. Start a new session, then invoke a skill such as `/ajigu-skills:write-ai-doc`.

### Individual skills

Ask your agent: "Install the app-icon-studio skill from https://github.com/huihuisang/ajigu-skills."

Install interactively with the Skills CLI:

```bash
npx skills add huihuisang/ajigu-skills -g
```

Install one skill without prompts:

```bash
npx skills add huihuisang/ajigu-skills -g -y --skill mobbin-search
```

Install every skill for every supported agent:

```bash
npx skills add huihuisang/ajigu-skills -g --all
```

You can also clone the repository and copy or symlink an individual directory under `skills/` into your agent's global skills directory.

Install the screenshot-localization Python dependencies when that skill is needed:

```bash
python3 -m pip install -r skills/localize-app-store-screenshots/requirements.txt
```

## Updates and existing installations

For the Codex bundle, refresh the marketplace and install its current plugin version:

```bash
codex plugin marketplace upgrade ajigu-skills
codex plugin add ajigu-skills@ajigu-skills
```

For Claude Code:

```bash
claude plugin marketplace update ajigu-skills
claude plugin update ajigu-skills@ajigu-skills
```

Restart or start a new session afterward. Maintainers must increment the plugin version in both manifests when shipping changes to the bundle, including skill changes. The validation script rejects mismatched versions. Individual Skills CLI installations remain separate and follow that installer's update workflow.

If skills are already installed individually, inspect the existing copies and preserve any local changes before switching to the bundle. The plugin does not remove or overwrite independent installations. Choose which installation to keep for each skill to avoid duplicate discovery; remove old copies only after confirming their contents and the replacement. Plugin skill names can have a host-specific namespace.

## Dependencies and initialization

Plugin installation registers workflows; it does not install Xcode, Python packages, command-line tools, signing identities, credentials, or service accounts. Follow the selected skill's prerequisites when needed. Some skills require macOS and local execution. Installing this plugin does not grant deletion, signing, or publication permission.

## Task output command

The plugin can invoke the bundled `skills/task-artifacts/scripts/task_artifacts.py` directly with Python 3.10+. The global launcher is optional. After explicitly choosing to initialize `task-artifacts`, run its `scripts/install.py` with Python 3.10+ to install the launcher and optional agent discovery links. The installer refuses unrelated existing commands and skills; it does not grant deletion permission or modify global instructions. See the [task-artifacts README](skills/task-artifacts/README.md) for migration, dependencies, and tests.

Installing any skill does not authorize deletion, signing changes, or publication. Use the authorization already given for the current task and ask before expanding its scope.

## Mobbin configuration

Never commit a real Mobbin API key or a personal 1Password item reference. Copy the example locally and point it at your own 1Password item:

```bash
cp skills/mobbin-search/mobbin.env.example skills/mobbin-search/mobbin.env
```

The repository ignores `mobbin.env`, downloaded `.mobbin/` results, Python bytecode, and common local metadata.

## Repository layout

```text
plugin.json
.agents/plugins/marketplace.json
.claude-plugin/plugin.json
.claude-plugin/marketplace.json
skills/
├── app-icon-studio/
├── disk-cleanup/
├── localize-app-store-screenshots/
├── macos-direct-distribution/
├── macos-finder-extension/
├── mobbin-search/
├── smooth-alpha-edges/
├── stock-value-analysis/
├── task-artifacts/
├── write-ai-doc/
└── xcode-cloud-setup/
```

Each directory is self-contained and includes a required `SKILL.md` plus only the scripts, references, assets, or agent metadata that its workflow needs.

## Validation

Requires Python 3.10+ for the checks, Codex CLI and Claude Code for plugin installation tests, and Node.js with npm for the standalone Skills CLI check. Integration checks run on macOS; other platforms are unverified.

```bash
python3 scripts/validate_plugins.py
python3 scripts/test_plugin_distribution.py
python3 scripts/verify_plugin_installation.py --output-dir /absolute/new-test-output
```

Use a new output directory outside this repository. The integration check creates isolated user profiles there, installs both bundles, compares every skill file, reads Codex's app-server skill inventory and Claude's component inventory, and installs only `write-ai-doc` through the Skills CLI. It leaves logs and profiles for inspection. It does not invoke a model, run the skills, or change the current user's plugin configuration. Network access is needed to resolve the Skills CLI package. Pass `--source huihuisang/ajigu-skills` to verify the published marketplace and its update commands; local-path marketplaces do not have a Git snapshot to upgrade.

The plugin formats follow the [OpenAI packaging guide](https://developers.openai.com/plugins/build/plugins) and [Claude plugin reference](https://code.claude.com/docs/en/plugins-reference).

## License

MIT
