"""Restore settings and commands share one operation deadline, including compensation."""
import unittest
from types import SimpleNamespace as NS
import movement_ui_fixture
movement_ui_fixture.install()
from apex_movement.panel_model import Model
from apex_movement.panel_transaction import Transaction


class Tests(unittest.TestCase):
    def test_command_failure_cannot_restart_the_fourteen_second_budget(self):
        now, confirmed, writes = [1], [None], []
        option = NS(identifier="dash", value=True, default_value=False,
                    confirm_write=lambda **_: confirmed[0])
        model = object.__new__(Model)
        model.mod = NS(save_settings=lambda: writes.append(option.value))
        model.options = {"dash": option}
        model.camera_options = {}
        model._undo, model._command_undo, model._command_plan = (), {}, None
        model.transaction = Transaction(model.mod, lambda *_: None, lambda: now[0])
        def command_failure(_, **_kwargs):
            confirmed[0] = None
            return False
        model.command_actions = NS(snapshot=lambda: {}, commands=NS(defaults=lambda: {}),
                                   apply=command_failure, prepare=command_failure)
        # No actual camera options: this fake command group needs no camera memory.
        model._start_global(((option, False),), "restore", ((option, True),), {}, {})
        now[0] = 12_000_000_001
        confirmed[0] = True
        self.assertIsNone(model.advance())
        self.assertTrue(model.transaction.pending)
        now[0] = 14_000_000_001
        self.assertEqual(model.advance(), "failed")
        self.assertFalse(model.transaction.pending)
        self.assertEqual(option.value, True)
        self.assertEqual(writes, [], "A failed Restore must never persist its first half")

    def test_abandoned_save_restores_prepared_bindings_without_another_save(self):
        now, confirmed, writes, bindings = [1], [None], [], {"key": "A"}
        option = NS(identifier="dash", value=True, default_value=False,
                    confirm_write=lambda **_: confirmed[0])
        model = object.__new__(Model)
        def fail_save():
            writes.append(dict(bindings))
            confirmed[0] = None
            raise OSError("private")
        model.mod = NS(save_settings=fail_save)
        model.options, model.camera_options = {"dash": option}, {}
        model._undo, model._command_undo, model._command_plan = (), {}, None
        model.transaction = Transaction(model.mod, lambda *_: None, lambda: now[0])
        model.command_actions = NS(prepare=lambda values, **_: bindings.update(values) or True)
        model._start_global(((option, False),), "restore", ((option, True),), {"key": "B"}, {"key": "A"})
        now[0] = 12_000_000_001
        confirmed[0] = True
        self.assertIsNone(model.advance())
        self.assertEqual(bindings, {"key": "B"})
        now[0] = 14_000_000_001
        self.assertEqual(model.advance(), "failed")
        self.assertEqual(option.value, True)
        self.assertEqual(bindings, {"key": "A"})
        self.assertEqual(writes, [{"key": "B"}])

    def test_real_command_restore_keeps_old_values_when_live_alignment_fails(self):
        from apex_movement.camera_control_actions import Actions
        from apex_camera_runtime.camera_commands import CameraCommands
        now, confirmed, writes = [1], [None], []
        option = NS(identifier="dash", value=True, default_value=False,
                    confirm_write=lambda **_: confirmed[0])
        commands = CameraCommands(third_person=lambda: None, shoulder=lambda: None,
                                  orbit=lambda: None, zoom_in=lambda: None, zoom_out=lambda: None,
                              camera_distance=lambda: None)
        previous_key = commands.option("orbit_key").value
        model = object.__new__(Model)
        def fail_save():
            writes.append(commands.option("orbit_key").value)
            confirmed[0] = None
            commands.align = lambda: (_ for _ in ()).throw(RuntimeError("private"))
            raise OSError("private")
        model.mod = NS(save_settings=fail_save)
        model.options, model.camera_options = {"dash": option}, {}
        model._undo, model._command_undo, model._command_plan = (), {}, None
        model.transaction = Transaction(model.mod, lambda *_: None, lambda: now[0])
        model.command_actions = Actions(commands, model.mod)
        previous_commands = model.command_actions.snapshot()
        model._start_global(((option, False),), "restore", ((option, True),),
                            {"orbit_key": "K"}, previous_commands)
        now[0], confirmed[0] = 12_000_000_001, True
        self.assertIsNone(model.advance())
        now[0] = 14_000_000_001
        self.assertEqual(model.advance(), "failed")
        self.assertEqual(commands.option("orbit_key").value, previous_key)
        self.assertEqual(writes, ["K"])


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
