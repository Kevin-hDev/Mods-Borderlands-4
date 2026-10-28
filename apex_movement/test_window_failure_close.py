"""Cleanup remains independent of character reads and failed cancellation gates."""
import importlib
import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace as NS

events = []
sdk = ModuleType("unrealsdk")
sdk.logging = NS(info=events.append)
sdk.hooks = NS(Type=NS(POST=1), remove_hook=lambda *_: None, has_hook=lambda *_: False)
sdk.commands = NS(remove_command=lambda *_: None, has_command=lambda *_: False)
sdk.find_enum = lambda _: NS(Default=0, DoNotLock=0)
sys.modules["unrealsdk"] = sdk
base = ModuleType("mods_base")
sys.modules["mods_base"] = base
package = ModuleType("_window_failure_contract")
package.__path__ = [str(Path(__file__).with_name("apex_movement"))]
sys.modules[package.__name__] = package
base.get_pc = lambda **_: pc
window = importlib.import_module(f"{package.__name__}.control_window")
cleanup = importlib.import_module(f"{package.__name__}.control_window_cleanup")


class Controller:
    bShowMouseCursor = True
    CurrentMouseCursor = 0
    broken = False
    @property
    def OakCharacter(self):
        if self.broken:
            raise RuntimeError("private")
        return self.current


character = NS()
pc = Controller()


class Tests(unittest.TestCase):
    def setUp(self):
        events.clear()
        pc.broken = False
        pc.current = character
        base.get_pc = window.get_pc = lambda **_: pc
        cleanup.get_pc = lambda **_: pc
        self.form = NS(focus=lambda: NS(), close_ready=lambda: False,
                       close_abort=lambda: events.append("aborted"))
        root = NS(RemoveFromParent=lambda: events.append("removed"))
        library = NS(SetInputMode_GameOnly=lambda *_: events.append("input_released"))
        self.item = window.Session(lambda: pc, lambda: root, lambda: library, False,
                                   self.form, NS(ready=lambda: True), lambda: character)
        self.item.input_changed = True
        window._active = self.item

    def assert_released(self):
        self.assertTrue(self.item.closed)
        self.assertIn("removed", events)
        self.assertIn("input_released", events)
        self.assertIsNone(window._active)

    def test_character_read_error_releases_current_controller_input(self):
        pc.broken = True
        self.item.close("command")
        self.assert_released()

    def test_abort_failure_still_releases_input(self):
        self.form.close_abort = lambda: (_ for _ in ()).throw(RuntimeError("private"))
        self.item.close_deadline = 0
        self.item.close("command")
        self.assert_released()

    def test_gate_failure_aborts_and_releases_input(self):
        self.form.close_ready = lambda: (_ for _ in ()).throw(RuntimeError("private"))
        self.item.close("command")
        self.assert_released()
        self.assertIn("aborted", events)

    def test_weak_controller_failure_does_not_retain_current_input(self):
        self.item.pc = lambda: (_ for _ in ()).throw(RuntimeError("private"))
        self.item.close("command")
        self.assert_released()

    def test_missing_weak_controller_does_not_retain_current_input(self):
        self.item.pc = lambda: None
        self.item.close("command")
        self.assert_released()

    def test_changed_character_does_not_release_new_world_input(self):
        pc.current = object()
        self.item.close("command")
        self.assertTrue(self.item.closed)
        self.assertIn("removed", events)
        self.assertNotIn("input_released", events)

    def test_failed_weak_read_does_not_release_another_controller(self):
        current = Controller()
        current.current = NS()
        window.get_pc = lambda **_: current
        base.get_pc = lambda **_: current
        cleanup.get_pc = lambda **_: current
        self.item.pc = lambda: (_ for _ in ()).throw(RuntimeError("private"))
        self.item.close("command")
        self.assertTrue(self.item.closed)
        self.assertNotIn("input_released", events)

    def test_close_uses_transaction_deadline_already_in_progress(self):
        self.form.close_deadline = lambda: 123
        self.item.close("command")
        self.assertEqual(self.item.close_deadline, 123)

    def test_failed_diagnostic_logger_cannot_block_input_release(self):
        original = sdk.logging.info
        self.addCleanup(setattr, sdk.logging, "info", original)
        sdk.logging.info = lambda *_: (_ for _ in ()).throw(RuntimeError("private"))
        pc.broken = True
        self.item.close("command")
        self.assert_released()


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
