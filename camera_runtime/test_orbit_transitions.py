"""Orbit owns no ThirdPerson layer and is restored through direct native requests."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.foot_mode import ORBIT_MODE  # noqa: E402
from apex_camera_runtime.constants import THIRD_PERSON_RIGHT as RIGHT  # noqa: E402
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
        return 70

    def ClientSetCameraMode(self, mode):
        self.client_modes.append(mode)
        self.PlayerCameraManager.mode = mode

    def CameraTransition(self, mode, *_args):
        self.PlayerCameraManager.mode = mode


actor = types.SimpleNamespace(ZoomState=types.SimpleNamespace(bWantsToZoom=False))
manager, bridge, hooks, settings = Manager(), Bridge(), Hooks(), Settings()
settings.orbit = True
pc = PC(actor, manager)
controller = ThirdPersonController(hooks, bridge, "orbit")
controller.sync("apex", pc, settings, 0)
check("saved Orbit starts without a hidden ThirdPerson layer",
      manager.pushes == 0 and controller._mode_pushes == 0 and pc.client_modes == [ORBIT_MODE])
check("Orbit suspends the shoulder bridge", bridge.suspended == [True])
check("the observed startup mode is confirmed", not controller.foot_mode.pending)

check("leaving Orbit succeeds", controller.toggle_orbit(settings, 1))
check("the shoulder bridge stays suspended until the Orbit exit is confirmed",
      bridge.suspended == [True])
check("the shoulder stays unchanged until the Orbit exit is confirmed",
      not controller.set_shoulder(settings, True) and not settings.left and bridge.rights == [RIGHT])
controller.sync("apex", pc, settings, 2)
check("leaving Orbit restores one ThirdPerson layer and shoulder",
      manager.pushes == 1 and controller._mode_pushes == 1 and not settings.orbit
      and bridge.suspended[-1] is False and not settings.left)
check("the shoulder becomes available after the Orbit exit is confirmed",
      controller.set_shoulder(settings, True) and settings.left and bridge.rights[-1] == -RIGHT)
check("entering Orbit succeeds", controller.toggle_orbit(settings, 3))
controller.sync("apex", pc, settings, 4)
check("entering Orbit removes every layer before the direct request",
      manager.pops == 1 and controller._mode_pushes == 0 and settings.orbit
      and pc.client_modes[-1] == ORBIT_MODE and bridge.suspended[-1] is True)


class FailingSettings(Settings):
    def __init__(self, orbit, rejected):
        super().__init__()
        self.orbit = orbit
        self.rejected = rejected

    def set_orbit(self, value):
        if value is self.rejected:
            raise RuntimeError("save refused")
        super().set_orbit(value)


save_manager, save_bridge = Manager(), Bridge()
save_settings = FailingSettings(True, False)
save_pc = PC(actor, save_manager)
save_controller = ThirdPersonController(Hooks(), save_bridge, "orbit_save")
save_controller.sync("apex", save_pc, save_settings, 3)
save_started = save_controller.toggle_orbit(save_settings, 4)
save_controller.sync("apex", save_pc, save_settings, 5)
check("a failed save while leaving Orbit keeps Orbit visible",
      save_started
      and save_manager.mode == ORBIT_MODE and save_controller._mode_pushes == 0
      and save_bridge.suspended[-1] is True and save_settings.orbit
      and save_settings.notes == ["Orbit Camera setting could not be saved."])
save_controller.stop()

enter_manager, enter_bridge = Manager(), Bridge()
enter_settings = FailingSettings(False, True)
enter_pc = PC(actor, enter_manager)
enter_controller = ThirdPersonController(Hooks(), enter_bridge, "orbit_enter_save")
enter_controller.sync("apex", enter_pc, enter_settings, 5)
enter_started = enter_controller.toggle_orbit(enter_settings, 6)
enter_controller.sync("apex", enter_pc, enter_settings, 7)
enter_controller.sync("apex", enter_pc, enter_settings, 8)
check("a failed save while entering Orbit keeps ThirdPerson visible",
      enter_started
      and enter_manager.mode == "ThirdPerson" and enter_controller._mode_pushes == 1
      and enter_bridge.suspended[-1] is False and not enter_settings.orbit
      and enter_settings.notes == ["Orbit Camera setting could not be saved."])
enter_controller.stop()

controller.stop()

ads_manager, ads_bridge, ads_hooks, ads_settings = Manager(), Bridge(), Hooks(), Settings()
ads_settings.orbit = True
ads_actor = types.SimpleNamespace(ZoomState=types.SimpleNamespace(bWantsToZoom=False))
ads_pc = PC(ads_actor, ads_manager)
ads = ThirdPersonController(ads_hooks, ads_bridge, "orbit_ads")
ads.sync("apex", ads_pc, ads_settings, 10)
ads_actor.ZoomState.bWantsToZoom = True
ads.sync("apex", ads_pc, ads_settings, 11)
check("Orbit ADS uses Default without a hidden layer",
      ads_manager.mode == "Default" and ads._mode_pushes == 0)
ads_actor.ZoomState.bWantsToZoom = False
ads.sync("apex", ads_pc, ads_settings, 12)
ads.sync("apex", ads_pc, ads_settings, 13)
check("ADS release restores Orbit directly and keeps its choice",
      ads_manager.mode == ORBIT_MODE and ads._mode_pushes == 0 and ads_settings.orbit)

vehicle_path = next(path for path in ads._transitions.paths
                    if path.endswith(":ServerCameraTransition"))
vehicle_callback = ads_hooks.items[(vehicle_path, "PRE", "orbit_ads")]
ads_actor.ZoomState.bWantsToZoom = True
ads.sync("apex", ads_pc, ads_settings, 14)
vehicle_callback(ads_pc, args("ThirdPersonVehicle"), None, Bound())
ads_manager.mode = "ThirdPersonVehicle"
ads.sync("apex", ads_pc, ads_settings, 15)
check("aim to vehicle creates no hidden ThirdPerson layer", ads._mode_pushes == 0)
ads_actor.ZoomState.bWantsToZoom = False
vehicle_callback(ads_pc, args("Default"), None, Bound())
ads.sync("apex", ads_pc, ads_settings, 16)
check("vehicle exit restores Orbit once and ends vehicle state",
      ads_manager.mode == ORBIT_MODE and not ads._in_vehicle and ads._mode_pushes == 0
      and "vehicle" not in ads._suspensions)

ads_manager.mode = "ThirdPersonVehicle"
ads.sync("apex", ads_pc, ads_settings, 17)
ads_manager.mode = ORBIT_MODE
ads.sync("apex", ads_pc, ads_settings, 18)
check("an observed vehicle exit also clears its suspension reason",
      not ads._in_vehicle and "vehicle" not in ads._suspensions)

before_restore = len(ads_pc.client_modes)
ads_manager.mode = "Slide"
ads.sync("apex", ads_pc, ads_settings, 19)
ads.sync("apex", ads_pc, ads_settings, 20)
check("observed Slide restores Orbit through one direct request",
      ads_manager.mode == ORBIT_MODE and len(ads_pc.client_modes) == before_restore + 1
      and not ads._recovery_requested)
ads.stop()
check("shutdown returns Orbit to Default and clears pending state",
      ads_manager.mode == "Default" and not ads.foot_mode.pending)


class RejectingPC(PC):
    def __init__(self, actor, manager):
        super().__init__(actor, manager)
        self.reject = True

    def ClientSetCameraMode(self, mode):
        self.client_modes.append(mode)
        if self.reject:
            raise RuntimeError("refused")
        self.PlayerCameraManager.mode = mode


fallback_manager, fallback_bridge, fallback_settings = Manager(), Bridge(), Settings()
fallback_settings.orbit = True
fallback_pc = RejectingPC(actor, fallback_manager)
fallback = ThirdPersonController(Hooks(), fallback_bridge, "orbit_fallback")
fallback.sync("apex", fallback_pc, fallback_settings, 100)
fallback.sync("apex", fallback_pc, fallback_settings, 200)
check("a refused startup falls back once without changing the saved choice",
      fallback_manager.pushes == 1 and fallback._mode_pushes == 1
      and fallback_settings.orbit and fallback_pc.client_modes == [ORBIT_MODE])
fallback_pc.reject = False
check("explicit F7 disables a refused saved choice", fallback.toggle_orbit(fallback_settings, 300))
check("disabling the refused choice keeps the fallback layer active",
      fallback_manager.pops == 0 and fallback_manager.mode == "ThirdPerson"
      and not fallback_settings.orbit and fallback._orbit_blocked_identity is None)
fallback.stop()

timeout_manager, timeout_bridge, timeout_settings = Manager(), Bridge(), Settings()
timeout_settings.orbit = True
timeout_pc = PC(actor, timeout_manager)
timeout_pc.ClientSetCameraMode = lambda mode: timeout_pc.client_modes.append(mode)
timeout = ThirdPersonController(Hooks(), timeout_bridge, "orbit_timeout")
timeout.sync("apex", timeout_pc, timeout_settings, 0)
timeout.sync("apex", timeout_pc, timeout_settings, 800_000_001)
check("an unconfirmed startup starts one tracked fallback layer",
      timeout.foot_mode.pending and timeout_manager.pushes == 1
      and timeout._mode_pushes == 1 and timeout_settings.orbit)
timeout.sync("apex", timeout_pc, timeout_settings, 800_000_002)
check("the visible fallback confirms before the controller becomes ready",
      not timeout.foot_mode.pending and timeout_manager.mode == "ThirdPerson")
timeout.stop()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
