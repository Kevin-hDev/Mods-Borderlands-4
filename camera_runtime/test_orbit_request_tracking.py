"""Every rewritten native return to Orbit joins the one pending request."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.foot_mode import CONFIRMATION_TIMEOUT_NS, ORBIT_MODE  # noqa: E402
from apex_camera_runtime.third_person import ThirdPersonController  # noqa: E402
from camera_test_fixtures import Bound, Bridge, Hooks, Manager, Settings, args  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class PC:
    def __init__(self, actor, manager):
        self.OakCharacter = actor
        self.PlayerCameraManager = manager
        self.client_modes = []

    def _get_address(self):
        return 802

    def ClientSetCameraMode(self, mode):
        self.client_modes.append(mode)


actor = types.SimpleNamespace(ZoomState=types.SimpleNamespace(bWantsToZoom=False))
manager, hooks, settings = Manager(), Hooks(), Settings()
settings.orbit = True
pc = PC(actor, manager)
controller = ThirdPersonController(hooks, Bridge(), "orbit_tracking")
controller.sync("apex", pc, settings, 0)
manager.mode = ORBIT_MODE
controller.sync("apex", pc, settings, 1)
check("startup confirmation leaves no request pending", not controller.foot_mode.pending)

path = next(path for path in controller._transitions.paths
            if path.endswith(":CameraTransition"))
callback = hooks.items[(path, "PRE", "orbit_tracking")]
first = callback(pc, args("Slide"), None, Bound())
check("a rewritten Slide records the Orbit request",
      first is hooks.Block and controller.foot_mode.pending
      and pc.client_modes == [ORBIT_MODE, ORBIT_MODE])
second = callback(pc, args("Default"), None, Bound())
check("another native return cannot duplicate the pending request",
      second is hooks.Block and pc.client_modes == [ORBIT_MODE, ORBIT_MODE])
manager.mode = ORBIT_MODE
controller.sync("apex", pc, settings, 2)
check("the tracked native return confirms through the normal frame path",
      not controller.foot_mode.pending and controller.foot_mode.confirmations == 2)
controller.stop()

blocked_manager, blocked_settings = Manager(), Settings()
blocked_settings.orbit = True
blocked_pc = PC(actor, blocked_manager)
blocked_bridge = Bridge()
blocked = ThirdPersonController(Hooks(), blocked_bridge, "orbit_refusal_toggle")
blocked.sync("apex", blocked_pc, blocked_settings, 0)
blocked.sync("apex", blocked_pc, blocked_settings, CONFIRMATION_TIMEOUT_NS + 1)
blocked.sync("apex", blocked_pc, blocked_settings, CONFIRMATION_TIMEOUT_NS + 2)
check("a refused saved Orbit choice falls back to ThirdPerson",
      blocked._desired_mode == "ThirdPerson" and blocked_manager.mode == "ThirdPerson"
      and blocked._orbit_blocked_identity == blocked._lifetime.ids)
check("the refusal is reported once", len(blocked_settings.notes) == 1)
suspensions = list(blocked_bridge.suspended)
blocked.sync("apex", blocked_pc, blocked_settings, CONFIRMATION_TIMEOUT_NS + 3)
check("a refused saved Orbit does not toggle native suspension every frame",
      blocked_bridge.suspended == suspensions)
check("the next Orbit command disables the saved choice without stopping the camera",
      blocked.toggle_orbit(blocked_settings, CONFIRMATION_TIMEOUT_NS + 4)
      and not blocked_settings.orbit and blocked.cleanup_pending
      and blocked._desired_mode == "ThirdPerson" and blocked_manager.mode == "ThirdPerson")
blocked.stop()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
raise SystemExit(1 if fails else 0)
