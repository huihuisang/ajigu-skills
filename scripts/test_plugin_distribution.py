"""Reject changes that break shared plugin identity or source containment."""

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from validate_plugins import FILES, validate


REPO = Path(__file__).resolve().parents[1]


class DistributionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='plugin-contract-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for name in FILES:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / name, target)
        shutil.copytree(REPO / 'skills', self.root / 'skills',
                        ignore=shutil.ignore_patterns('__pycache__', '.DS_Store'))

    def change(self, name, mutate):
        file = self.root / name
        value = json.loads(file.read_text(encoding='utf-8'))
        mutate(value)
        file.write_text(json.dumps(value), encoding='utf-8')

    def test_current_package_contains_every_skill(self):
        expected = sorted(p.parent.name for p in (REPO / 'skills').glob('*/SKILL.md'))
        self.assertEqual(validate(self.root)['skills'], expected)

    def test_version_drift_is_rejected(self):
        self.change('.claude-plugin/plugin.json', lambda d: d.update(version='9.0.0'))
        with self.assertRaisesRegex(ValueError, 'version'):
            validate(self.root)

    def test_codex_source_escape_is_rejected(self):
        self.change('.agents/plugins/marketplace.json',
                    lambda d: d['plugins'][0]['source'].update(path='../elsewhere'))
        with self.assertRaisesRegex(ValueError, 'repository root'):
            validate(self.root)

    def test_claude_source_escape_is_rejected(self):
        self.change('.claude-plugin/marketplace.json',
                    lambda d: d['plugins'][0].update(source='../elsewhere'))
        with self.assertRaisesRegex(ValueError, 'repository root'):
            validate(self.root)

    def test_alternate_skill_copy_is_rejected(self):
        self.change('.claude-plugin/plugin.json', lambda d: d.update(skills='./copied-skills/'))
        with self.assertRaisesRegex(ValueError, 'shared skills'):
            validate(self.root)

    def test_automatic_hooks_are_rejected(self):
        self.change('.claude-plugin/plugin.json', lambda d: d.update(hooks='./hooks/hooks.json'))
        with self.assertRaisesRegex(ValueError, 'skills-only'):
            validate(self.root)

    def test_openai_tools_are_rejected(self):
        self.change('plugin.json', lambda d: d['extensions']['com.openai'].update(apps='./.app.json'))
        with self.assertRaisesRegex(ValueError, 'presentation'):
            validate(self.root)

    def test_automatically_discovered_hooks_are_rejected(self):
        (self.root / 'hooks').mkdir()
        (self.root / 'hooks/hooks.json').write_text('{}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'automatically discovered'):
            validate(self.root)


if __name__ == '__main__':
    unittest.main()
