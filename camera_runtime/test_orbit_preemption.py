"""ADS and vehicles preempt an unfinished explicit Orbit choice."""

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


class DelayedPC:
    def __init__(self, address, actor, manager):
        self.address = address
        self.OakCharacter = actor
        self.PlayerCameraManager = manager
        self.client_modes = []
        self.transitions = []
        self.vehicle_immediate = True

    def _get_address(self):
        return self.address

    def ClientSetCameraMode(self, mode):
        self.client_modes.append(mode)
        if mode == "Default" or (mode == "ThirdPersonVehicle" and self.vehicle_immediate):
            self.PlayerCameraManager.mode = mode

    def CameraTransition(self, mode, *_args):
        self.transitions.append(mode)
        self.PlayerCameraManager.mode = mode


aim_actor = types.SimpleNamespace(ZoomState=types.SimpleNamespace(bWantsToZoom=False))
aim_manager, aim_settings = Manager(), Settings()
aim_pc = DelayedPC(901, aim_actor, aim_manager)
aim = ThirdPersonController(Hooks(), Bridge(), "orbit_preempt_aim")
aim.sync("apex", aim_pc, aim_settings, 0)
check("the delayed Orbit choice starts", aim.toggle_orbit(aim_settings, 1))
aim_actor.ZoomState.bWantsToZoom = True
aim.sync("apex", aim_pc, aim_settings, 2)
check("ADS cancels the unsaved choice and immediately obtains Default",
      not aim.foot_mode.pending and not aim_settings.orbit and aim._aiming
      and aim._desired_mode == THIRD_PERSON_MODE and aim_manager.mode == "Default")
aim_manager.mode = ORBIT_MODE
aim.sync("apex", aim_pc, aim_settings, 3)
check("a late Orbit response cannot replace ADS",
      aim_manager.mode == "Default" and aim_pc.transitions == ["Default", "Default"])
aim_actor.ZoomState.bWantsToZoom = False
aim.sync("apex", aim_pc, aim_settings, 4)
aim.sync("apex", aim_pc, aim_settings, 5)
check("releasing ADS restores the choice that existed before F7",
      aim_manager.mode == THIRD_PERSON_MODE and not aim_settings.orbit
      and aim._mode_pushes == 1)
aim.stop()

exit_aim_actor = types.SimpleNamespace(ZoomState=types.SimpleNamespace(bWantsToZoom=False))
exit_aim_manager, exit_aim_settings = Manager(), Settings()
exit_aim_settings.orbit = True
exit_aim_pc = DelayedPC(904, exit_aim_actor, exit_aim_manager)
exit_aim = ThirdPersonController(Hooks(), Bridge(), "orbit_exit_preempt_aim")
exit_aim.sync("apex", exit_aim_pc, exit_aim_settings, 6)
exit_aim_manager.mode = ORBIT_MODE
exit_aim.sync("apex", exit_aim_pc, exit_aim_settings, 7)
exit_aim.toggle_orbit(exit_aim_settings, 8)
exit_aim_actor.ZoomState.bWantsToZoom = True
exit_aim.sync("apex", exit_aim_pc, exit_aim_settings, 9)
check("ADS also cancels a delayed Orbit exit and keeps the saved Orbit choice",
      exit_aim._aiming and exit_aim._desired_mode == ORBIT_MODE
      and exit_aim._mode_pushes == 0 and exit_aim_settings.orbit)
exit_aim_manager.mode = THIRD_PERSON_MODE
exit_aim.sync("apex", exit_aim_pc, exit_aim_settings, 10)
check("a late ThirdPerson response cannot replace ADS", exit_aim_manager.mode == "Default")
exit_aim_actor.ZoomState.bWantsToZoom = False
exit_aim.sync("apex", exit_aim_pc, exit_aim_settings, 11)
exit_aim_manager.mode = ORBIT_MODE
exit_aim.sync("apex", exit_aim_pc, exit_aim_settings, 12)
exit_aim.sync("apex", exit_aim_pc, exit_aim_settings, 13)
check("ADS release restores the pre-F7 Orbit choice",
      not exit_aim._aiming and not exit_aim._aim_returning
      and not exit_aim.foot_mode.pending and exit_aim_settings.orbit)
exit_aim.stop()

vehicle_actor = types.SimpleNamespace(ZoomState=types.SimpleNamespace(bWantsToZoom=False))
vehicle_manager, vehicle_settings, vehicle_hooks = Manager(), Settings(), Hooks()
vehicle_pc = DelayedPC(902, vehicle_actor, vehicle_manager)
vehicle = ThirdPersonController(vehicle_hooks, Bridge(), "orbit_preempt_vehicle")
vehicle.sync("apex", vehicle_pc, vehicle_settings, 10)
check("the vehicle case starts one delayed Orbit choice",
      vehicle.toggle_orbit(vehicle_settings, 11))
vehicle_manager.mode = "ThirdPersonVehicle"
vehicle.sync("apex", vehicle_pc, vehicle_settings, 12)
check("an observed vehicle cancels the choice without touching its visible mode",
      vehicle._in_vehicle and not vehicle.foot_mode.pending and not vehicle_settings.orbit
      and vehicle._desired_mode == THIRD_PERSON_MODE and vehicle._mode_pushes == 0
      and vehicle_manager.mode == "ThirdPersonVehicle")
vehicle_manager.mode = ORBIT_MODE
vehicle.sync("apex", vehicle_pc, vehicle_settings, 13)
check("a late Orbit response cannot masquerade as vehicle exit",
      vehicle._in_vehicle and vehicle_manager.mode == "ThirdPersonVehicle"
      and vehicle_pc.client_modes[-1] == "ThirdPersonVehicle" and not vehicle_settings.orbit)
vehicle.sync("apex", vehicle_pc, vehicle_settings, 14)
vehicle_manager.mode = THIRD_PERSON_MODE
vehicle.sync("apex", vehicle_pc, vehicle_settings, 15)
vehicle.sync("apex", vehicle_pc, vehicle_settings, 16)
check("an observed exit without a hook rebuilds the pre-F7 choice",
      not vehicle._in_vehicle and vehicle._mode_pushes == 1
      and vehicle_manager.mode == THIRD_PERSON_MODE)
vehicle.stop()

exit_actor = types.SimpleNamespace(ZoomState=types.SimpleNamespace(bWantsToZoom=False))
exit_manager, exit_settings = Manager(), Settings()
exit_settings.orbit = True
exit_pc = DelayedPC(903, exit_actor, exit_manager)
exit = ThirdPersonController(Hooks(), Bridge(), "orbit_exit_preempt_vehicle")
exit.sync("apex", exit_pc, exit_settings, 20)
exit_manager.mode = ORBIT_MODE
exit.sync("apex", exit_pc, exit_settings, 21)
check("a delayed Orbit exit starts", exit.toggle_orbit(exit_settings, 22))
exit_manager.mode = "ThirdPersonVehicle"
exit.sync("apex", exit_pc, exit_settings, 23)
check("an observed vehicle preserves Orbit as the prior saved choice",
      exit._in_vehicle and exit._desired_mode == ORBIT_MODE and exit._mode_pushes == 1)
exit_manager.mode = THIRD_PERSON_MODE
exit.sync("apex", exit_pc, exit_settings, 24)
check("a late ThirdPerson response is replaced by the vehicle mode",
      exit._in_vehicle and exit_manager.mode == "ThirdPersonVehicle")
exit.sync("apex", exit_pc, exit_settings, 25)
exit_manager.mode = ORBIT_MODE
exit.sync("apex", exit_pc, exit_settings, 26)
check("the real exit removes the hidden layer and requests Orbit again",
      not exit._in_vehicle and exit._mode_pushes == 0 and exit.foot_mode.pending)
exit_manager.mode = ORBIT_MODE
exit.sync("apex", exit_pc, exit_settings, 27)
check("the pre-vehicle Orbit choice is confirmed without changing the setting",
      not exit.foot_mode.pending and exit_settings.orbit and exit._desired_mode == ORBIT_MODE)
exit.stop()

recovery_aim_actor = types.SimpleNamespace(ZoomState=types.SimpleNamespace(bWantsToZoom=False))
recovery_aim_manager, recovery_aim_settings = Manager(), Settings()
recovery_aim_pc = DelayedPC(906, recovery_aim_actor, recovery_aim_manager)
recovery_aim = ThirdPersonController(Hooks(), Bridge(), "orbit_recovery_preempt_aim")
recovery_aim.sync("apex", recovery_aim_pc, recovery_aim_settings, 28)
recovery_aim_manager.mode = ORBIT_MODE
recovery_aim.sync("apex", recovery_aim_pc, recovery_aim_settings, 29)
recovery_aim_actor.ZoomState.bWantsToZoom = True
recovery_aim.sync("apex", recovery_aim_pc, recovery_aim_settings, 30)
check("ADS preempts an unfinished internal foot-mode recovery",
      recovery_aim._aiming and not recovery_aim.foot_mode.pending
      and recovery_aim_manager.mode == "Default")
recovery_aim.stop()

recovery_vehicle_actor = types.SimpleNamespace(ZoomState=types.SimpleNamespace(bWantsToZoom=False))
recovery_vehicle_manager, recovery_vehicle_settings = Manager(), Settings()
recovery_vehicle_pc = DelayedPC(907, recovery_vehicle_actor, recovery_vehicle_manager)
recovery_vehicle = ThirdPersonController(
    Hooks(), Bridge(), "orbit_recovery_preempt_vehicle")
recovery_vehicle.sync("apex", recovery_vehicle_pc, recovery_vehicle_settings, 31)
recovery_vehicle_manager.mode = ORBIT_MODE
recovery_vehicle.sync("apex", recovery_vehicle_pc, recovery_vehicle_settings, 32)
recovery_vehicle_manager.mode = "ThirdPersonVehicle"
recovery_vehicle.sync("apex", recovery_vehicle_pc, recovery_vehicle_settings, 33)
check("a vehicle preempts an unfinished internal foot-mode recovery",
      recovery_vehicle._in_vehicle and not recovery_vehicle.foot_mode.pending
      and recovery_vehicle_manager.mode == "ThirdPersonVehicle")
recovery_vehicle.stop()

stuck_actor = types.SimpleNamespace(ZoomState=types.SimpleNamespace(bWantsToZoom=False))
stuck_manager, stuck_settings = Manager(), Settings()
stuck_pc = DelayedPC(905, stuck_actor, stuck_manager)
stuck = ThirdPersonController(Hooks(), Bridge(), "orbit_vehicle_timeout")
stuck.sync("apex", stuck_pc, stuck_settings, 30)
stuck.toggle_orbit(stuck_settings, 31)
stuck_manager.mode = "ThirdPersonVehicle"
stuck.sync("apex", stuck_pc, stuck_settings, 32)
stuck_pc.vehicle_immediate = False
stuck_manager.mode = ORBIT_MODE
stuck.sync("apex", stuck_pc, stuck_settings, 33)
check("an asynchronous vehicle reassertion is tracked", stuck._vehicle_reassert_ns == 33)
stuck.sync("apex", stuck_pc, stuck_settings, 33 + CONFIRMATION_TIMEOUT_NS + 1)
check("an unconfirmed vehicle reassertion stops safely in Default",
      not stuck.cleanup_pending and stuck_manager.mode == "Default")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
raise SystemExit(1 if fails else 0)
