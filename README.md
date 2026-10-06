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

## Task output command

After installing `task-artifacts`, run its `scripts/install.py` with Python 3.10+ to install the launcher and optional agent discovery links. The installer refuses unrelated existing commands and skills; it does not grant deletion permission or modify global instructions. See the [task-artifacts README](skills/task-artifacts/README.md) for migration, dependencies, and tests.

Installing any skill does not authorize deletion, signing changes, or publication. Use the authorization already given for the current task and ask before expanding its scope.

## Mobbin configuration

Never commit a real Mobbin API key or a personal 1Password item reference. Copy the example locally and point it at your own 1Password item:

```bash
cp skills/mobbin-search/mobbin.env.example skills/mobbin-search/mobbin.env
```

The repository ignores `mobbin.env`, downloaded `.mobbin/` results, Python bytecode, and common local metadata.

## Repository layout

```text
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

## License

MIT
