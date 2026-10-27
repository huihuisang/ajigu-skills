"""Install both plugin bundles and one standalone skill in isolated profiles."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from validate_plugins import validate
from codex_skill_inventory import inventory


REPO = Path(__file__).resolve().parents[1]


def skill_files(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((root / 'skills').rglob('*')) if p.is_file()
            and p.name != '.DS_Store' and '__pycache__' not in p.parts}


def verify(output, source):
    local_source = Path(source).is_dir()
    if local_source:
        source = str(Path(source).resolve())
    output = output.resolve()
    if output == REPO or output.is_relative_to(REPO):
        raise ValueError('Keep installation profiles outside the repository.')
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    workspace = output / 'workspace'
    workspace.mkdir()
    contract = validate(REPO)
    expected = skill_files(REPO)
    logs = []

    def environment(label):
        home = output / label
        home.mkdir(mode=0o700)
        (home / '.codex').mkdir()
        env = dict(os.environ, HOME=str(home), CODEX_HOME=str(home / '.codex'),
                   CLAUDE_CONFIG_DIR=str(home / '.claude'), XDG_CONFIG_HOME=str(home / '.config'),
                   XDG_CACHE_HOME=str(home / '.cache'), XDG_DATA_HOME=str(home / '.local/share'),
                   NPM_CONFIG_CACHE=str(output / 'npm-cache'), NPM_CONFIG_UPDATE_NOTIFIER='false',
                   GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0',
                   DISABLE_TELEMETRY='1', CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1',
                   PYTHONDONTWRITEBYTECODE='1')
        for key in ('CLAUDECODE', 'CLAUDE_CODE_ENTRYPOINT', 'TASK_ARTIFACT_HOME', 'TASK_ARTIFACT_SKILL_DIR'):
            env.pop(key, None)
        return home, env

    def run(label, args, env):
        result = subprocess.run(args, cwd=workspace, env=env, text=True,
                                capture_output=True, timeout=60)
        (output / (label + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
        logs.append({'check': label, 'exit_code': result.returncode})
        print(label, result.returncode, flush=True)
        if result.returncode:
            raise RuntimeError(f'{label} failed; inspect {output / (label + ".log")}')
        return result.stdout

    def compare_installed(path, home):
        path = path.resolve()
        if not path.is_relative_to(home):
            raise ValueError('The plugin installer wrote outside its isolated profile.')
        if skill_files(path) != expected:
            raise ValueError('Installed skill files differ from repository sources.')
        if (home / '.local/bin/task-artifacts').exists():
            raise ValueError('Plugin installation must not initialize task-artifacts.')

    codex_home, codex_env = environment('codex-profile')
    run('codex-marketplace-add', ['codex', 'plugin', 'marketplace', 'add', source, '--json'], codex_env)
    install = json.loads(run('codex-plugin-add', ['codex', 'plugin', 'add',
                              'ajigu-skills@ajigu-skills', '--json'], codex_env))
    compare_installed(Path(install['installedPath']), codex_home)
    listing = json.loads(run('codex-plugin-list', ['codex', 'plugin', 'list',
                              '--marketplace', 'ajigu-skills', '--json'], codex_env))
    if not any(p['pluginId'] == 'ajigu-skills@ajigu-skills' and p['enabled']
               for p in listing['installed']):
        raise ValueError('Codex did not enable the installed plugin.')
    runtime = inventory(workspace, codex_env, output)
    loaded = [skill for item in runtime['data'] for skill in item['skills']
              if skill.get('pluginId') == 'ajigu-skills@ajigu-skills']
    if sorted(skill['name'] for skill in loaded if skill['enabled']) != [
            'ajigu-skills:' + name for name in contract['skills']]:
        raise ValueError('Codex did not load every plugin skill.')
    if any(item.get('errors') for item in runtime['data']):
        raise ValueError('Codex reported errors while loading skills.')
    logs.append({'check': 'codex-runtime-inventory', 'exit_code': 0})
    if not local_source:
        run('codex-marketplace-upgrade', ['codex', 'plugin', 'marketplace', 'upgrade', 'ajigu-skills'], codex_env)
    run('codex-plugin-reinstall', ['codex', 'plugin', 'add', 'ajigu-skills@ajigu-skills', '--json'], codex_env)

    claude_home, claude_env = environment('claude-profile')
    run('claude-marketplace-add', ['claude', 'plugin', 'marketplace', 'add', source], claude_env)
    run('claude-plugin-install', ['claude', 'plugin', 'install',
                                'ajigu-skills@ajigu-skills', '--json'], claude_env)
    receipt = json.loads((claude_home / '.claude/plugins/installed_plugins.json').read_text(encoding='utf-8'))
    installed = receipt['plugins']['ajigu-skills@ajigu-skills'][0]
    compare_installed(Path(installed['installPath']), claude_home)
    details = run('claude-plugin-details', ['claude', 'plugin', 'details', 'ajigu-skills'], claude_env)
    match = re.search(r'Skills \((\d+)\)\s+([^\n]+)', details)
    if not match or int(match.group(1)) != len(contract['skills']):
        raise ValueError('Claude loaded an unexpected skill count.')
    if sorted(match.group(2).strip().split(', ')) != contract['skills']:
        raise ValueError('Claude loaded different skill identities.')
    if not local_source:
        run('claude-marketplace-update', ['claude', 'plugin', 'marketplace', 'update', 'ajigu-skills'], claude_env)
        run('claude-plugin-update', ['claude', 'plugin', 'update', 'ajigu-skills@ajigu-skills'], claude_env)

    single_home, single_env = environment('standalone-profile')
    run('standalone-skill-install', ['npx', '--yes', 'skills', 'add', str(REPO),
        '--global', '--agent', 'codex', '--copy', '--yes', '--skill', 'write-ai-doc'], single_env)
    names = sorted(p.name for p in (single_home / '.agents/skills').iterdir() if p.is_dir())
    if names != ['write-ai-doc']:
        raise ValueError('Standalone installation unexpectedly included other skills.')
    source_skill = REPO / 'skills/write-ai-doc/SKILL.md'
    if source_skill.read_bytes() != (single_home / '.agents/skills/write-ai-doc/SKILL.md').read_bytes():
        raise ValueError('Standalone skill differs from repository source.')
    summary = {'source': source, 'contract': contract, 'checks': logs,
               'skill_file_count': len(expected), 'skill_sha256': expected,
               'versions': {tool: subprocess.check_output([tool, '--version'], text=True, env=env).strip()
                            for tool, env in [('codex', codex_env), ('claude', claude_env)]},
               'marketplace_updates': 'Not applicable to a local-path source.' if local_source else 'Passed.',
               'scope': 'CLI installation and component inventory; no model invocation or desktop UI test.'}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True, type=Path, help='New directory outside the repository.')
    parser.add_argument('--source', default=str(REPO), help='Marketplace source; defaults to this checkout.')
    args = parser.parse_args()
    verify(args.output_dir, args.source)
