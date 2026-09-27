"""A failed Orbit save confirms its visible rollback or stops the camera unit."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.constants import ORBIT_MODE, THIRD_PERSON_MODE  # noqa: E402
from apex_camera_runtime.foot_mode import CONFIRMATION_TIMEOUT_NS  # noqa: E402
from apex_camera_runtime.third_person import ThirdPersonController  # noqa: E402
from camera_test_fixtures import Bridge, Hooks, Manager, Settings  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class FailingOrbitSettings(Settings):
    def set_orbit(self, value):
        if value:
            raise RuntimeError("save refused")
        super().set_orbit(value)


class DeferredPushManager(Manager):
    def __init__(self, refuse=False):
        super().__init__()
        self.refuse = refuse
        self.defer = False

    def PushActorCameraMode(self, _actor, mode, *_args):
        self.pushes += 1
        if self.defer and self.refuse and mode == THIRD_PERSON_MODE:
            raise RuntimeError("push refused")
        if not self.defer:
            self.mode = mode


class PC:
    def __init__(self, address, actor, manager):
        self.address = address
        self.OakCharacter = actor
        self.PlayerCameraManager = manager
        self.client_modes = []

    def _get_address(self):
        return self.address

    def ClientSetCameraMode(self, mode):
        self.client_modes.append(mode)
        if mode == "Default":
            self.PlayerCameraManager.mode = mode


def started(address, refuse=False):
    actor = types.SimpleNamespace(ZoomState=types.SimpleNamespace(bWantsToZoom=False))
    manager = DeferredPushManager(refuse)
    settings = FailingOrbitSettings()
    pc = PC(address, actor, manager)
    bridge = Bridge()
    controller = ThirdPersonController(Hooks(), bridge, f"orbit_rollback_{address}")
    controller.sync("apex", pc, settings, 0)
    manager.defer = True
    return controller, pc, manager, settings, bridge


controller, pc, manager, settings, bridge = started(904)
check("entry request starts", controller.toggle_orbit(settings, 1))
manager.mode = ORBIT_MODE
controller.sync("apex", pc, settings, 2)
check("a rejected save starts a tracked ThirdPerson rollback",
      controller.foot_mode.pending and manager.mode == ORBIT_MODE and not settings.orbit
      and bridge.suspended[-1] is True)
manager.mode = THIRD_PERSON_MODE
controller.sync("apex", pc, settings, 3)
check("the rollback ends only after ThirdPerson is observed",
      not controller.foot_mode.pending and controller.cleanup_pending and bridge.suspended[-1] is False)
controller.stop()

timeout, timeout_pc, timeout_manager, timeout_settings, _ = started(905)
timeout.toggle_orbit(timeout_settings, 1)
timeout_manager.mode = ORBIT_MODE
timeout.sync("apex", timeout_pc, timeout_settings, 2)
timeout.sync("apex", timeout_pc, timeout_settings, CONFIRMATION_TIMEOUT_NS + 3)
check("an unconfirmed rollback stops safely in Default",
      not timeout.cleanup_pending and timeout_manager.mode == "Default"
      and timeout_pc.client_modes[-1] == "Default" and not timeout.foot_mode.pending)

refused, refused_pc, refused_manager, refused_settings, _ = started(906, refuse=True)
refused.toggle_orbit(refused_settings, 1)
refused_manager.mode = ORBIT_MODE
refused.sync("apex", refused_pc, refused_settings, 2)
check("a refused rollback also stops safely in Default",
      not refused.cleanup_pending and refused_manager.mode == "Default"
      and refused_pc.client_modes[-1] == "Default" and not refused.foot_mode.pending)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
raise SystemExit(1 if fails else 0)
