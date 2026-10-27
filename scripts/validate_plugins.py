"""Check the shared source and metadata contract for both plugin hosts."""

import argparse
import json
from pathlib import Path
import re


FILES = ('plugin.json', '.claude-plugin/plugin.json',
         '.agents/plugins/marketplace.json', '.claude-plugin/marketplace.json')


def validate(root):
    portable, claude, codex_market, claude_market = [
        json.loads((root / name).read_text(encoding='utf-8')) for name in FILES
    ]
    if portable.get('$schema') != 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json':
        raise ValueError('Unsupported portable plugin schema.')
    for field in ('name', 'version', 'description', 'author', 'repository', 'license'):
        if not portable.get(field) or portable[field] != claude.get(field):
            raise ValueError(f'Plugin metadata differs: {field}')
    if not re.fullmatch(r'\d+\.\d+\.\d+', portable['version']):
        raise ValueError('Use a stable semantic version for this plugin.')
    if claude.get('skills') != './skills/':
        raise ValueError('Claude must use the shared skills directory.')
    for manifest in (portable, claude):
        if any(key in manifest for key in ('hooks', 'mcpServers', 'apps', 'userConfig')):
            raise ValueError('This distribution must remain skills-only.')
    for path in ('hooks', '.mcp.json', 'mcp.json', '.app.json'):
        if (root / path).exists():
            raise ValueError(f'Unexpected automatically discovered component: {path}')
    overlay = portable.get('extensions', {}).get('com.openai', {})
    if set(overlay) != {'interface'}:
        raise ValueError('OpenAI settings must contain only presentation metadata.')
    name = portable['name']
    for catalog in (codex_market, claude_market):
        if catalog.get('name') != name or len(catalog.get('plugins', [])) != 1:
            raise ValueError('Both marketplaces must expose one complete plugin.')
        if catalog['plugins'][0].get('name') != name:
            raise ValueError('Marketplace plugin identity differs.')
    if codex_market['plugins'][0].get('source') != {'source': 'local', 'path': './'}:
        raise ValueError('Codex must load the repository root.')
    if claude_market['plugins'][0].get('source') != './':
        raise ValueError('Claude must load the repository root.')
    if codex_market['plugins'][0].get('policy') != {
            'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'}:
        raise ValueError('Unexpected Codex installation policy.')
    if claude_market.get('owner') != portable['author']:
        raise ValueError('Marketplace publisher differs.')
    skills = []
    for file in sorted((root / 'skills').glob('*/SKILL.md')):
        match = re.search(r'^name:\s*(.+?)\s*$', file.read_text(encoding='utf-8'), re.M)
        if not match or match.group(1) != file.parent.name:
            raise ValueError(f'Skill identity differs: {file.parent.name}')
        skills.append(file.parent.name)
    if not skills:
        raise ValueError('The plugin contains no skills.')
    if list(root.glob('plugins/**/SKILL.md')):
        raise ValueError('Do not duplicate skill sources into plugin subdirectories.')
    return {'name': name, 'version': portable['version'], 'skills': skills}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.root), indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f'Validation failed: {error}\n')
