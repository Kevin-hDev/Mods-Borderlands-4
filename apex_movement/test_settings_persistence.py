"""All mod writers keep the previous file when serialization or replacement fails."""
import importlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from settings_persistence_test_fixtures import save_successfully

import movement_ui_fixture
movement_ui_fixture.install()


class Tests(unittest.TestCase):
    def setUp(self):
        try:
            self.persistence = importlib.import_module("apex_movement.settings_persistence")
        except ModuleNotFoundError:
            self.fail("Atomic persistence is not installed")
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "settings.json"
        self.path.write_text('{"old": true}')
        class SDK:
            def save_settings(mod):
                if mod.recursive:
                    mod.save_settings()
                if mod.empty:
                    mod.settings_file.unlink(missing_ok=True)
                    return
                with mod.settings_file.open("w") as target:
                    json.dump(mod.values, target)
        class Mod(self.persistence.AtomicSettingsMixin, SDK):
            pass
        self.mod = Mod()
        self.mod.settings_file = self.path
        self.mod.values = {"new": True}
        self.mod.empty = self.mod.recursive = False

    def assert_intact(self):
        self.assertEqual(self.path.read_text(), '{"old": true}')
        self.assertEqual(self.mod.settings_file, self.path)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_serialization_failure_does_not_truncate_old_file(self):
        self.mod.values = {"first": True, "bad": object()}
        with self.assertRaises(TypeError):
            self.mod.save_settings()
        self.assert_intact()

    def test_replace_failure_has_no_direct_write_fallback(self):
        with patch.object(self.persistence.os, "replace", side_effect=PermissionError("private")):
            with self.assertRaises(PermissionError):
                self.mod.save_settings()
        self.assert_intact()

    def test_success_replaces_file_and_restores_sdk_path(self):
        self.mod.save_settings()
        self.assertEqual(json.loads(self.path.read_text()), {"new": True})
        self.assertEqual(self.mod.settings_file, self.path)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_sdk_empty_settings_still_removes_the_old_file(self):
        self.mod.empty = True
        self.mod.save_settings()
        self.assertFalse(self.path.exists())
        self.assertEqual(self.mod.settings_file, self.path)

    def test_nested_save_fails_closed_without_recursion(self):
        self.mod.recursive = True
        with self.assertRaises(RuntimeError):
            self.mod.save_settings()
        self.assert_intact()

    def test_no_settings_file_preserves_sdk_no_save_behavior(self):
        self.mod.settings_file = None
        self.mod.save_settings()
        self.assertEqual(self.path.read_text(), '{"old": true}')

    def test_committed_save_does_not_attempt_cleanup_of_moved_temporary(self):
        with patch.object(Path, "unlink", side_effect=PermissionError("private")):
            save_successfully(self)
        self.assertEqual(json.loads(self.path.read_text()), {"new": True})

    def test_missing_parent_fails_without_changing_sdk_path(self):
        self.mod.settings_file = self.path.parent / "missing" / "settings.json"
        original = self.mod.settings_file
        with self.assertRaises(FileNotFoundError):
            self.mod.save_settings()
        self.assertEqual(self.mod.settings_file, original)
        self.assertEqual(self.path.read_text(), '{"old": true}')

    def test_empty_sdk_save_does_not_retry_already_removed_temporary(self):
        self.mod.empty = True
        unlink = Path.unlink
        removed = set()
        def once(path, *args, **kwargs):
            if path in removed:
                raise PermissionError("private")
            removed.add(path)
            return unlink(path, *args, **kwargs)
        with patch.object(Path, "unlink", once):
            self.mod.save_settings()
        self.assertFalse(self.path.exists())


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
