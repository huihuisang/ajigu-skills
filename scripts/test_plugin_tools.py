"""Exercise explicit tool setup without copying or removing skill directories."""

import json
import os
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest
from unittest.mock import patch

from install_plugin_tools import install


class PluginToolTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='plugin-tools-')
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name) / 'user'
        self.home.mkdir()
        self.source = self.package('0.1.1')

    def package(self, version):
        root = self.home / 'plugins' / version
        root.mkdir(parents=True)
        (root / 'plugin.json').write_text(json.dumps({
            'name': 'ajigu-skills', 'version': version,
            'repository': 'https://github.com/huihuisang/ajigu-skills'}), encoding='utf-8')
        script = root / 'skills/task-artifacts/scripts/task_artifacts.py'
        script.parent.mkdir(parents=True)
        script.write_text(f'print({version!r})\n', encoding='utf-8')
        return root

    def invoke(self, home=None):
        home = home or self.home
        return subprocess.check_output([str(home / '.local/bin/task-artifacts'), '--help'],
                                       env=dict(os.environ, HOME=str(home)), text=True).strip()

    def test_only_plugin_alias_and_launcher_are_installed(self):
        install(self.source, self.home)
        self.assertEqual(self.invoke(), '0.1.1')
        alias = self.home / '.local/share/ajigu-skills/current'
        self.assertEqual(alias.resolve(), self.source)
        self.assertFalse(os.path.isabs(os.readlink(alias)))
        self.assertFalse((self.home / '.agents/skills').exists())
        self.assertFalse((self.home / '.codex/skills').exists())
        self.assertFalse((self.home / '.claude/skills').exists())

    def test_reinstall_and_version_switch(self):
        install(self.source, self.home)
        install(self.source, self.home)
        newer = self.package('0.1.2')
        install(newer, self.home)
        self.assertEqual(self.invoke(), '0.1.2')

    def test_failed_launcher_update_restores_previous_alias(self):
        install(self.source, self.home)
        newer = self.package('0.1.2')
        original_replace = os.replace
        command = self.home / '.local/bin/task-artifacts'

        def fail_command(source, destination):
            if destination == command:
                raise OSError('Simulated launcher failure')
            return original_replace(source, destination)

        with patch('install_plugin_tools.os.replace', side_effect=fail_command):
            with self.assertRaisesRegex(OSError, 'Simulated launcher failure'):
                install(newer, self.home)
        self.assertEqual(self.invoke(), '0.1.1')

    def test_home_relocation(self):
        install(self.source, self.home)
        target = self.home.with_name('other-user')
        self.home.rename(target)
        self.assertEqual(self.invoke(target), '0.1.1')

    def test_symlinked_data_parent(self):
        redirected = self.home / 'data/deeper/share'
        redirected.mkdir(parents=True)
        (self.home / '.local').mkdir()
        (self.home / '.local/share').symlink_to(redirected, target_is_directory=True)
        install(self.source, self.home)
        self.assertEqual(self.invoke(), '0.1.1')

    def test_upgrade_after_old_cache_is_removed(self):
        install(self.source, self.home)
        newer = self.package('0.1.2')
        shutil.rmtree(self.source)
        install(newer, self.home)
        self.assertEqual(self.invoke(), '0.1.2')

    def test_unowned_dangling_link_is_preserved(self):
        alias = self.home / '.local/share/ajigu-skills/current'
        alias.parent.mkdir(parents=True)
        alias.symlink_to(self.home / 'missing')
        with self.assertRaisesRegex(ValueError, 'unrelated plugin link'):
            install(self.source, self.home)
        self.assertEqual(os.readlink(alias), str(self.home / 'missing'))

    def test_unrelated_command_is_preserved_before_alias_changes(self):
        command = self.home / '.local/bin/task-artifacts'
        command.parent.mkdir(parents=True)
        command.write_text('unrelated command', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'unrelated command'):
            install(self.source, self.home)
        self.assertEqual(command.read_text(), 'unrelated command')
        self.assertFalse((self.home / '.local/share/ajigu-skills/current').exists())

    def test_legacy_owned_launcher_can_be_replaced(self):
        command = self.home / '.local/bin/task-artifacts'
        command.parent.mkdir(parents=True)
        command.write_text('#!/bin/sh\n# task-artifacts portable launcher\n', encoding='utf-8')
        original = self.home / '.agents/skills/task-artifacts/SKILL.md'
        original.parent.mkdir(parents=True)
        original.write_text('local changes', encoding='utf-8')
        install(self.source, self.home)
        self.assertEqual(self.invoke(), '0.1.1')
        self.assertEqual(original.read_text(), 'local changes')

    def test_unrelated_alias_is_preserved(self):
        alias = self.home / '.local/share/ajigu-skills/current'
        alias.parent.mkdir(parents=True)
        outside = self.home / 'unrelated'
        outside.mkdir()
        alias.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'unrelated plugin link'):
            install(self.source, self.home)
        self.assertEqual(alias.resolve(), outside)

    def test_real_directory_at_alias_is_preserved(self):
        alias = self.home / '.local/share/ajigu-skills/current'
        alias.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'directory'):
            install(self.source, self.home)
        self.assertTrue(alias.is_dir())


if __name__ == '__main__':
    unittest.main()
