"""Stopping an unfinished Orbit exit clears it and returns the native camera to Default."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.constants import ORBIT_MODE  # noqa: E402
from apex_camera_runtime.third_person import ThirdPersonController  # noqa: E402
from camera_test_fixtures import Bridge, Hooks, Manager, Settings  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class DeferredPushManager(Manager):
    def PushActorCameraMode(self, _actor, _mode, *_args):
        self.pushes += 1


class PC:
    def __init__(self, actor, manager):
        self.OakCharacter = actor
        self.PlayerCameraManager = manager
        self.client_modes = []
        self.fail_default = False

    def _get_address(self):
        return 903

    def ClientSetCameraMode(self, mode):
        self.client_modes.append(mode)
        if mode == "Default" and self.fail_default:
            raise RuntimeError("default refused")
        if mode == "Default":
            self.PlayerCameraManager.mode = mode


actor = types.SimpleNamespace(ZoomState=types.SimpleNamespace(bWantsToZoom=False))
manager, settings = DeferredPushManager(), Settings()
settings.orbit = True
pc = PC(actor, manager)
controller = ThirdPersonController(Hooks(), Bridge(), "orbit_cleanup_pending")
controller.sync("apex", pc, settings, 0)
manager.mode = ORBIT_MODE
controller.sync("apex", pc, settings, 1)
check("saved Orbit was confirmed before the exit", not controller.foot_mode.pending)
check("the deferred exit starts", controller.toggle_orbit(settings, 2))
check("the exit is still pending while Orbit remains visible",
      controller.foot_mode.pending and manager.mode == ORBIT_MODE)
controller.stop(now_ns=3)
check("stop explicitly returns Default and clears the unfinished transaction",
      pc.client_modes[-1] == "Default" and manager.mode == "Default"
      and not controller.foot_mode.pending and not controller.cleanup_pending)

retry_manager, retry_settings = DeferredPushManager(), Settings()
retry_settings.orbit = True
retry_pc = PC(actor, retry_manager)
retry = ThirdPersonController(Hooks(), Bridge(), "orbit_cleanup_retry")
retry.sync("apex", retry_pc, retry_settings, 10)
retry_manager.mode = ORBIT_MODE
retry.sync("apex", retry_pc, retry_settings, 11)
retry_pc.fail_default = True
try:
    retry.stop(now_ns=12)
except RuntimeError:
    pass
check("a refused Default keeps one cleanup authority for a retry",
      retry.cleanup_pending and retry.foot_mode.rollback_failed)
retry_pc.fail_default = False
retry.stop(now_ns=13)
check("the later cleanup retry reaches Default and releases the authority",
      retry_manager.mode == "Default" and not retry.cleanup_pending)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
raise SystemExit(1 if fails else 0)
