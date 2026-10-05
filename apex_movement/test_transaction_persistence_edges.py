"""Concurrent runtime saves cannot escape transaction compensation."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

import movement_ui_fixture
movement_ui_fixture.install()
from apex_movement.panel_transaction import Transaction, TRANSACTION_TIMEOUT_NS
from apex_movement import panel_persistence
from apex_camera_runtime.camera_option import CameraBoolOption


class Tests(unittest.TestCase):
    def test_runtime_save_during_wait_is_compensated_after_final_save_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            path.write_text("90")
            fov = NS(identifier="fov", value=90)
            orbit = CameraBoolOption("orbit", False, route=lambda _: True, cancel=lambda: True)
            orbit.mod = NS(is_enabled=True)
            writes = []
            def save():
                writes.append(fov.value)
                if len(writes) == 2:
                    raise OSError("private")
                path.write_text(str(fov.value))
            transaction = Transaction(NS(settings_file=path, save_settings=save), lambda *_: None)
            transaction.start(((fov, 100), (orbit, True)), ((fov, 90), (orbit, False)), "write")
            save()  # Runtime remembers native FOV while Orbit is still pending.
            orbit.commit(True)
            result = transaction.advance()
            if result is None:
                orbit.commit(False)
                result = transaction.advance()
            self.assertFalse(result[2])
            self.assertEqual(fov.value, 90)
            self.assertEqual(path.read_text(), "90")

    def test_retry_success_keeps_original_camera_timeout(self):
        now, saves = [1], []
        option = CameraBoolOption("orbit", False, route=lambda _: True, cancel=lambda: True)
        option.mod = NS(is_enabled=True)
        def save():
            saves.append(True)
            if len(saves) == 1:
                raise OSError("private")
        transaction = Transaction(NS(save_settings=save), lambda *_: None, lambda: now[0])
        transaction.start(((option, True),), ((option, False),), "write")
        now[0] += TRANSACTION_TIMEOUT_NS + 1
        self.assertIsNone(transaction.advance())
        now[0] += TRANSACTION_TIMEOUT_NS + 1
        self.assertFalse(transaction.advance()[2])
        self.assertEqual(transaction.failure_reason, "camera_timeout")

    def test_fingerprint_missing_file_and_size_bound(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            mod = NS(settings_file=path)
            before = panel_persistence.fingerprint(mod)
            self.assertTrue(panel_persistence.unchanged(mod, before))
            path.write_bytes(b"a" * (panel_persistence.MAX_SETTINGS_BYTES + 1))
            self.assertIsNone(panel_persistence.fingerprint(mod))
            self.assertFalse(panel_persistence.unchanged(mod, before))

    def test_camera_timeout_with_exhausted_persistence_reports_save_failure(self):
        now = [1]
        option = CameraBoolOption("orbit", False, route=lambda _: True, cancel=lambda: True)
        option.mod = NS(is_enabled=True)
        def fail():
            raise OSError("private")
        transaction = Transaction(NS(save_settings=fail), lambda *_: None, lambda: now[0])
        transaction.start(((option, True),), ((option, False),), "write")
        now[0] += TRANSACTION_TIMEOUT_NS + 1
        self.assertIsNone(transaction.advance())
        now[0] = 30_000_000_000
        self.assertFalse(transaction.advance()[2])
        self.assertEqual(transaction.failure_reason, "failed")

    def test_read_failure_reports_only_type_once(self):
        from apex_movement import report
        messages = []
        mod = NS(settings_file=Path("private"))
        report.reset()
        with patch.object(Path, "open", side_effect=PermissionError("private path")), \
                patch.object(report.logging, "error", side_effect=messages.append):
            panel_persistence.fingerprint(mod, report.error_once)
            panel_persistence.fingerprint(mod, report.error_once)
        self.assertEqual(len(messages), 1)
        self.assertIn("Settings read failed: PermissionError", messages[0])
        self.assertNotIn("private", messages[0])


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
