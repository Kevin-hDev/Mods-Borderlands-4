"""Optional orphan cleanup cannot prevent SDK saves or weaken their atomic protection."""
import json
import unittest
from unittest.mock import patch

from settings_persistence_test_fixtures import PersistenceCase, WindowsReader
import test_settings_persistence_cleanup as cleanup_cases


class Tests(PersistenceCase):
    child = cleanup_cases.Tests.child

    def warnings(self, messages):
        from unrealsdk import logging
        return patch.object(logging, "warning", messages.append)

    def test_refused_scan_warns_once_across_startup_enable_and_disable_saves(self):
        messages, scans = [], []
        legacy = self.path.with_name("a" * 32 + ".tmp")
        legacy.write_text("keep")
        private_error = PermissionError(f"SECRET location={self.path}")
        def refused(_parent):
            scans.append(True)
            raise private_error
        with self.warnings(messages), patch.object(self.persistence.os, "scandir", refused):
            for phase in ("startup", "enabled", "disabled"):
                self.mod.values = {"phase": phase}
                self.save_successfully()
                self.assertTrue(self.path.is_file())
                self.assertEqual(json.loads(self.path.read_text()), {"phase": phase})
        self.assertEqual(len(scans), 1)
        self.assertEqual(len(messages), 1)
        self.assertIn("PermissionError", messages[0])
        self.assertNotIn("SECRET", messages[0])
        self.assertNotIn(str(self.path), messages[0])
        self.assertTrue(legacy.is_file())
        self.assertEqual(legacy.read_text(), "keep")
        self.assertEqual(self.mod.settings_file, self.path)
        self.assertFalse(self.mod._settings_save_active)
        if __name__ == "__main__":
            print("OBSERVED SDK WARNING:", messages[0])

    def test_real_locked_orphan_is_kept_while_current_settings_are_saved(self):
        orphan = self.child()
        reader = WindowsReader(orphan)
        self.addCleanup(reader.close)
        messages = []
        with self.warnings(messages):
            self.save_successfully()
            self.mod.values = {"second": True}
            self.save_successfully()
        self.assertTrue(orphan.is_file())
        self.assertEqual(orphan.read_text(), '{"incomplete":')
        self.assertTrue(self.path.is_file())
        self.assertEqual(json.loads(self.path.read_text()), {"second": True})
        self.assertEqual(len(messages), 1)
        self.assertIn("PermissionError", messages[0])
        self.assertNotIn(str(orphan), messages[0])
        if __name__ == "__main__":
            print("OBSERVED NATIVE WINDOWS CLEANUP WARNING:", messages[0])

    def test_cleanup_failure_still_preserves_old_bytes_on_actual_serialization_failure(self):
        messages = []
        self.mod.values = {"good": True, "bad": object()}
        with self.warnings(messages), patch.object(self.persistence.os, "scandir",
                                                  side_effect=PermissionError("SECRET")):
            self.save_failing(TypeError)
            self.assertTrue(self.path.is_file())
            self.assertEqual(self.path.read_text(), '{"old": true}')
            self.assertEqual(self.mod.settings_file, self.path)
            self.assertFalse(self.mod._settings_save_active)
            self.mod.values = {"retry": True}
            self.save_successfully()
        self.assertTrue(self.path.is_file())
        self.assertEqual(json.loads(self.path.read_text()), {"retry": True})
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])
        self.assertEqual(len(messages), 1)

    def test_unexpected_cleanup_error_is_optional_and_reported_by_type_only(self):
        messages = []
        with self.warnings(messages), patch.object(self.persistence, "_cleanup_orphans",
                                                  side_effect=RuntimeError("SECRET")):
            self.save_successfully()
        self.assertTrue(self.path.is_file())
        self.assertEqual(json.loads(self.path.read_text()), {"new": True})
        self.assertEqual(len(messages), 1)
        self.assertIn("RuntimeError", messages[0])
        self.assertNotIn("SECRET", messages[0])


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
