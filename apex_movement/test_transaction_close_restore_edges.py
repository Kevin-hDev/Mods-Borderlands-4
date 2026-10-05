"""A valid closing context restores camera state and camera-only Undo stays honest."""
import unittest
from types import SimpleNamespace as NS

import movement_ui_fixture
movement_ui_fixture.install()
from apex_movement import control_window_transaction_close as close
from apex_movement.panel_transaction import Transaction, TRANSACTION_TIMEOUT_NS
from apex_movement.panel_restore import Restore


class Tests(unittest.TestCase):
    def test_expired_close_with_valid_context_advances_restoring_gate(self):
        restores = []
        form = NS(close_ready=lambda: restores.append(True) or True,
                  close_abort=lambda: self.fail("Valid context was logically aborted"))
        session = NS(close_deadline=0, same_context=lambda _: True, pc=lambda: object(),
                     form=form, deferred_close="command")
        self.assertFalse(close.defer(session, "command"))
        self.assertEqual(restores, [True])

    def test_camera_only_undo_losing_ownership_reports_partial_success(self):
        model = Restore()
        option = NS(identifier="orbit", value=False)
        model._undo = ((option, True),)
        model._command_undo = {"orbit_key": "K"}
        model.options = {"orbit": option}
        model.camera_options = {"orbit": option}
        model.camera_elsewhere = True
        self.assertTrue(model.undo())
        self.assertEqual(model.success_notice, "undone_partial")
        self.assertEqual(model._undo, ())
        self.assertFalse(option.value)

    def test_already_target_but_pending_camera_times_out_with_camera_reason(self):
        now = [1]
        option = NS(identifier="orbit", value=True, camera_status="pending")
        option.cancel_pending = lambda: setattr(option, "camera_status", "confirmed") or True
        transaction = Transaction(NS(save_settings=lambda: None), lambda *_: None, lambda: now[0])
        self.assertIsNone(transaction.start(((option, True),), ((option, False),), "write"))
        now[0] += TRANSACTION_TIMEOUT_NS + 1
        self.assertFalse(transaction.advance()[2])
        self.assertEqual(transaction.failure_reason, "camera_timeout")

    def test_waiting_route_retries_then_times_out_with_camera_reason(self):
        now = [1]
        class Waiting:
            identifier = "orbit"
            camera_status = "confirmed"
            _value = False
            @property
            def value(self):
                return self._value
            @value.setter
            def value(self, value):
                self.camera_status = "waiting" if value else "confirmed"
                if not value:
                    self._value = value
            def cancel_pending(self):
                self.camera_status = "confirmed"
                return True
        option = Waiting()
        transaction = Transaction(NS(save_settings=lambda: None), lambda *_: None, lambda: now[0])
        self.assertIsNone(transaction.start(((option, True),), ((option, False),), "write"))
        self.assertIsNone(transaction.advance())
        now[0] += TRANSACTION_TIMEOUT_NS + 1
        self.assertFalse(transaction.advance()[2])
        self.assertEqual(transaction.failure_reason, "camera_timeout")


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
