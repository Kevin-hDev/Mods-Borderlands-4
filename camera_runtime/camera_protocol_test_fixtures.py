"""Exercise real camera adapters with an inert legacy authority; no game DLL is loaded."""
import importlib
import sys
from types import ModuleType

from apex_camera_runtime.shared import ALL_STATES, STATE, IncompatibleState
from apex_camera_runtime.constants import PROTOCOL


def refuses_legacy(test, package, settings_name):
    legacy = ModuleType("_apex_camera_runtime_v1")
    legacy.protocol, legacy.runtime = 1, object()
    saved = {name: sys.modules[name] for name in ALL_STATES if name in sys.modules}
    for name in ALL_STATES:
        sys.modules.pop(name, None)
    sys.modules[legacy.__name__] = legacy
    try:
        try:
            camera = importlib.import_module(f"{package}.camera")
            settings = importlib.import_module(f"{package}.{settings_name}")
            if package == "apex_movement":
                importlib.import_module(f"{package}.pack").CARRIES = ()
            settings.third_person.value = True
            refused = camera.start()
            for frame in range(3):
                camera.on_frame(frame)
        except RuntimeError as error:
            test.fail(f"Mixed protocols must refuse only camera work: {type(error).__name__}")
        test.assertFalse(camera._registered)
        test.assertIsInstance(refused, IncompatibleState)
        test.assertIn(f"expected_protocol={PROTOCOL}", refused.message)
        test.assertIn("loaded_protocols=1", refused.message)
        test.assertIsNone(camera._runtime)
        test.assertFalse(camera.ready())
        test.assertFalse(camera.toggle_third_person())
        test.assertTrue(settings.third_person.value)
        test.assertFalse(settings.framing.confirm())
        test.assertTrue(camera.elected_elsewhere())
        test.assertEqual(camera.aim_status()[0], "camera_outdated")
        test.assertEqual(camera.framing_status(), "camera_outdated")
        test.assertIs(sys.modules[legacy.__name__], legacy)
        test.assertNotIn(STATE, sys.modules)
        camera.stop()
    finally:
        for name in ALL_STATES:
            sys.modules.pop(name, None)
        sys.modules.update(saved)
