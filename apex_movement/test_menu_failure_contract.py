"""Keep persistence, native timeout and unsafe closure failures distinct."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

import movement_ui_fixture
movement_ui_fixture.install()
from apex_movement.panel_transaction import Transaction, TRANSACTION_TIMEOUT_NS
from apex_camera_runtime.camera_option import CameraBoolOption


class Tests(unittest.TestCase):
    def test_failed_open_restores_memory_and_bindings_without_retrying_disk(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            path.write_text('{"dash": true}', encoding="utf-8")
            writes, bindings = [], {"key": "A"}
            option = NS(identifier="dash", value=True)
            def save():
                writes.append(option.value)
                raise PermissionError("private")
            def prepare(restoring):
                bindings["key"] = "A" if restoring else "B"
                return True
            transaction = Transaction(NS(settings_file=path, save_settings=save), lambda *_: None)
            result = transaction.start(((option, False),), ((option, True),), "restore", finalize=prepare)
            self.assertIsNotNone(result, "An unchanged settings file must not trigger repeated writes")
            self.assertFalse(result[2])
            self.assertEqual(option.value, True)
            self.assertEqual(bindings, {"key": "A"})
            self.assertEqual(writes, [False])
            self.assertEqual(path.read_text(encoding="utf-8"), '{"dash": true}')
            self.assertEqual(transaction.failure_reason, "failed")

    def test_native_wait_timeout_has_camera_reason_after_confirmed_restoration(self):
        now = [1]
        option = CameraBoolOption("orbit", False, route=lambda _: True, cancel=lambda: True)
        option.mod = NS(is_enabled=True)
        transaction = Transaction(NS(save_settings=lambda: None), lambda *_: None, lambda: now[0])
        self.assertIsNone(transaction.start(((option, True),), ((option, False),), "write"))
        now[0] += TRANSACTION_TIMEOUT_NS + 1
        result = transaction.advance()
        self.assertFalse(result[2])
        self.assertEqual(option.value, False)
        self.assertEqual(transaction.failure_reason, "camera_timeout")

    def test_confirmation_timeout_does_not_claim_disk_failure(self):
        now, confirms = [1], [None]
        option = NS(identifier="camera_framing_zoom", value=15,
                    confirm_write=lambda restoring=False: True if restoring else confirms[0])
        transaction = Transaction(NS(save_settings=lambda: None), lambda *_: None, lambda: now[0])
        self.assertIsNone(transaction.start(((option, 25),), ((option, 15),), "write"))
        now[0] += TRANSACTION_TIMEOUT_NS + 1
        self.assertFalse(transaction.advance()[2])
        self.assertEqual(transaction.failure_reason, "camera_timeout")

    def test_partial_sdk_write_is_compensated_instead_of_assumed_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            path.write_text("true", encoding="utf-8")
            writes = []
            option = NS(identifier="dash", value=True)
            def save():
                writes.append(option.value)
                with path.open("w", encoding="utf-8") as target:
                    if len(writes) == 1:
                        target.write("{")
                        raise OSError("private")
                    target.write("true" if option.value else "false")
            transaction = Transaction(NS(settings_file=path, save_settings=save), lambda *_: None)
            self.assertFalse(transaction.start(((option, False),), ((option, True),), "write")[2])
            self.assertEqual(writes, [False, True])
            self.assertEqual(path.read_text(encoding="utf-8"), "true")

    def test_repeated_write_failure_keeps_write_reason_when_local_recovery_confirmed(self):
        now = [1]
        option = NS(identifier="dash", value=True)
        def save():
            raise OSError("private")
        transaction = Transaction(NS(save_settings=save), lambda *_: None, lambda: now[0])
        transaction.start(((option, False),), ((option, True),), "write")
        now[0] = 30_000_000_000
        self.assertFalse(transaction.advance()[2])
        self.assertEqual(option.value, True)
        self.assertEqual(transaction.failure_reason, "failed")

    def test_failed_native_cancel_still_restores_local_camera_option_on_abort(self):
        option = NS(identifier="orbit", value=True, camera_status="pending")
        option.cancel_pending = lambda **_: (_ for _ in ()).throw(RuntimeError("private"))
        option.commit = lambda value: setattr(option, "value", value)
        option.reject = lambda: setattr(option, "camera_status", "refused")
        transaction = Transaction(NS(save_settings=lambda: self.fail("Aborted change was saved")), lambda *_: None)
        self.assertIsNone(transaction.start(((option, True),), ((option, False),), "write"))
        self.assertFalse(transaction.abort()[2])
        self.assertFalse(option.value, "A failed native cancel must not skip local restoration")
        self.assertEqual(transaction.failure_reason, "rollback_abandoned")


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
