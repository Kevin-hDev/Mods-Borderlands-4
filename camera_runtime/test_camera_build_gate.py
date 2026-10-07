"""No camera activation before qualification; the native profile owns its target."""
import ctypes
import types
import unittest

from apex_camera_runtime.native_bridge import Bridge, Config
from camera_test_fixtures import Hooks, Manager, Settings, Bridge as FakeBridge
from apex_camera_runtime.third_person import ThirdPersonController


class Function:
    def __init__(self, result=0):
        self.result, self.calls = result, []

    def __call__(self, *args):
        self.calls.append(args)
        return self.result


class BuildGateTests(unittest.TestCase):
    def test_waiting_never_pushes_mode_or_installs_hooks(self):
        ready = [False]
        manager = Manager()
        pc = types.SimpleNamespace(OakCharacter=object(), PlayerCameraManager=manager)
        native = FakeBridge()
        controller = ThirdPersonController(Hooks(), native, "test", readiness=lambda: ready[0])
        for frame in range(120):
            controller.sync("test", pc, Settings(), frame)
        self.assertFalse(controller.cleanup_pending)
        self.assertNotEqual(manager.mode, "ThirdPerson")
        ready[0] = True
        controller.sync("test", pc, Settings(), 121)
        self.assertEqual(manager.mode, "ThirdPerson")
        controller.stop()

    def test_native_selected_epic_target_replaces_the_steam_default(self):
        library = types.SimpleNamespace(**{name: Function() for name in (
            "view_start", "view_stop", "view_set_suspended", "view_set_right", "view_stats")})
        library.view_update_rva = Function(0x3CC9ECA)
        api = Bridge(library)
        config_values = []
        library.view_start = lambda _pointer, config: config_values.append(
            ctypes.cast(config, ctypes.POINTER(Config)).contents.expected_rva) or 0
        self.assertTrue(api.start(types.SimpleNamespace(_get_address=lambda: 0x10000), 48.4))
        self.assertEqual(config_values, [0x3CC9ECA])

    def test_unqualified_native_target_never_starts(self):
        library = types.SimpleNamespace(**{name: Function() for name in (
            "view_start", "view_stop", "view_set_suspended", "view_set_right", "view_stats", "view_update_rva")})
        api = Bridge(library)
        with self.assertRaises(RuntimeError):
            api.start(types.SimpleNamespace(_get_address=lambda: 0x10000), 48.4)
        self.assertEqual(library.view_start.calls, [])


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
