# Ajigu Skills

A portable collection of reusable agent skills for App Store operations, UI research, image cleanup, equity analysis, and Xcode Cloud.

## Skills

| Skill | Purpose | Optional dependencies |
| --- | --- | --- |
| `localize-app-store-screenshots` | Localize text in existing App Store screenshots while preserving product imagery. | Python 3, Pillow, NumPy, OpenCV; `asc`, `asc-shots-pipeline`, and `asc-cli-usage` for upload workflows |
| `mobbin-search` | Search Mobbin for real product screenshots and download results for visual analysis. | Python 3, a Mobbin API key; 1Password CLI for the recommended secret workflow |
| `smooth-alpha-edges` | Repair jagged transparent-image silhouettes while preserving interior pixels. | Bash, ImageMagick |
| `stock-value-analysis` | Analyze long-term equity value with structured history, recent filings, and anomaly-driven research. | Internet access and market-data sources |
| `xcode-cloud-setup` | Audit, configure, and diagnose Xcode Cloud workflows. | `asc`, `jq`, App Store Connect authentication |

## Install

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

## Mobbin configuration

Never commit a real Mobbin API key or a personal 1Password item reference. Copy the example locally and point it at your own 1Password item:

```bash
cp skills/mobbin-search/mobbin.env.example skills/mobbin-search/mobbin.env
```

The repository ignores `mobbin.env`, downloaded `.mobbin/` results, Python bytecode, and common local metadata.

## Repository layout

```text
skills/
├── localize-app-store-screenshots/
├── mobbin-search/
├── smooth-alpha-edges/
├── stock-value-analysis/
└── xcode-cloud-setup/
```

Each directory is self-contained and includes a required `SKILL.md` plus only the scripts, references, assets, or agent metadata that its workflow needs.

## License

MIT
