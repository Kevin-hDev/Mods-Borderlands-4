"""Aiming temporarily yields to native first person without growing the mode stack."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.third_person import ThirdPersonController  # noqa: E402
from camera_test_fixtures import Bound, Bridge, Hooks, Manager, Settings, args  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def player(address, actor, manager):
    calls = []

    def transition(*values):
        calls.append(values)
        manager.mode = values[0]

    return types.SimpleNamespace(_get_address=lambda: address, OakCharacter=actor,
                                 PlayerCameraManager=manager, CameraTransition=transition,
                                 camera_transitions=calls)


zoom = types.SimpleNamespace(bWantsToZoom=False)
actor = types.SimpleNamespace(ZoomState=zoom)
manager, bridge = Manager(), Bridge()
pc = player(30, actor, manager)
controller = ThirdPersonController(Hooks(), bridge, identifier="ads")
settings = Settings()

controller.sync("apex_movement", pc, settings, 1)
slide_path = next(path for path in controller._transitions.paths
                  if path.endswith(":CameraTransition"))
slide_callback = controller.hooks.items[(slide_path, "PRE", "ads")]
slide_call = Bound()
slide_callback(pc, args("Slide"), None, slide_call)
check("a slide before aiming is initially kept in third person",
      slide_call.calls[0][0] == "ThirdPerson")
zoom.bWantsToZoom = True
controller.sync("apex_movement", pc, settings, 2)
check("aiming removes the one owned third-person mode and suspends the shift",
      manager.mode == "Default" and manager.pushes == 1 and manager.pops == 1
      and controller._mode_pushes == 0 and bridge.suspended[-1] is True
      and pc.camera_transitions == [("Default", "Default", 0.0, True, True)])

controller.sync("apex_movement", pc, settings, 3)
check("holding aim does not repeat mode or bridge changes",
      manager.pushes == 1 and manager.pops == 1 and bridge.suspended == [True])

zoom.bWantsToZoom = False
controller.sync("apex_movement", pc, settings, 4)
check("releasing aim restores exactly one third-person mode before the shift",
      manager.mode == "ThirdPerson" and manager.pushes == 2 and manager.pops == 1
      and controller._mode_pushes == 1 and bridge.suspended == [True])
controller.sync("apex_movement", pc, settings, 5)
check("the shift resumes only after third person is observed",
      bridge.suspended == [True, False] and manager.pushes == 2)

controller.sync("apex_movement", pc, settings, 6)
check("steady third person stays balanced", manager.pushes == 2 and manager.pops == 1)
controller.stop()
check("shutdown removes the final owned mode", manager.pushes == manager.pops == 2)

vehicle_actor = types.SimpleNamespace(ZoomState=types.SimpleNamespace(bWantsToZoom=False))
vehicle_manager, vehicle_bridge, vehicle_hooks = Manager(), Bridge(), Hooks()
vehicle_pc = player(31, vehicle_actor, vehicle_manager)
vehicle = ThirdPersonController(vehicle_hooks, vehicle_bridge, identifier="ads_vehicle")
vehicle.sync("apex_movement", vehicle_pc, settings, 10)
vehicle_actor.ZoomState.bWantsToZoom = True
vehicle.sync("apex_movement", vehicle_pc, settings, 11)
server_path = next(path for path in vehicle._transitions.paths
                   if path.endswith(":ServerCameraTransition"))
callback = vehicle_hooks.items[(server_path, "PRE", "ads_vehicle")]
callback(vehicle_pc, args("ThirdPersonVehicle"), None, Bound())
vehicle_manager.mode = "ThirdPersonVehicle"
vehicle.sync("apex_movement", vehicle_pc, settings, 12)
check("entering a vehicle from aim restores one owned on-foot mode underneath it",
      vehicle_manager.pushes == 2 and vehicle_manager.pops == 1
      and vehicle._mode_pushes == 1 and vehicle_bridge.suspended == [True])
vehicle_actor.ZoomState.bWantsToZoom = False
callback(vehicle_pc, args("Default"), None, Bound())
vehicle_manager.mode = "ThirdPerson"
vehicle.sync("apex_movement", vehicle_pc, settings, 13)
check("vehicle exit still resumes the third-person shift after aim",
      vehicle_bridge.suspended[-1] is False and vehicle_manager.pushes == 2)
vehicle.stop()
check("aim-to-vehicle shutdown keeps the stack balanced",
      vehicle_manager.pushes == vehicle_manager.pops == 2)

retry_clock = [20]
retry_actor = types.SimpleNamespace(ZoomState=types.SimpleNamespace(bWantsToZoom=False))
retry_manager, retry_bridge, retry_hooks = Manager(), Bridge(), Hooks()
retry_pc = player(32, retry_actor, retry_manager)
retry = ThirdPersonController(retry_hooks, retry_bridge, identifier="ads_retry",
                              clock=lambda: retry_clock[0])
retry.sync("apex_movement", retry_pc, settings, retry_clock[0])
retry_actor.ZoomState.bWantsToZoom = True
retry.sync("apex_movement", retry_pc, settings, 21)
retry_bridge.fail_stop = True
settings.enabled = False
try:
    retry.sync("apex_movement", retry_pc, settings, 22)
except RuntimeError:
    pass
retry_bridge.fail_stop = False
settings.enabled = True
retry_clock[0] = 100_000_022
retry.sync("apex_movement", retry_pc, settings, retry_clock[0])
check("a failed stop during aim is cleaned before rebuilding the camera unit",
      retry_bridge.starts == 2 and retry._hooks_installed and retry._aiming
      and retry._mode_pushes == 0)
retry.stop()

observed_actor = types.SimpleNamespace(ZoomState=types.SimpleNamespace(bWantsToZoom=False))
observed_manager, observed_bridge = Manager(), Bridge()
observed_pc = player(33, observed_actor, observed_manager)
observed = ThirdPersonController(Hooks(), observed_bridge, identifier="ads_observed_vehicle")
observed.sync("apex_movement", observed_pc, settings, 30)
observed_actor.ZoomState.bWantsToZoom = True
observed.sync("apex_movement", observed_pc, settings, 31)
observed_manager.mode = "ThirdPersonVehicle"
observed.sync("apex_movement", observed_pc, settings, 32)
check("an observed vehicle entry ends aim without rebuilding over the vehicle camera",
      observed._in_vehicle and not observed._aiming and observed._mode_pushes == 0
      and observed_manager.pushes == 1 and observed_bridge.suspended == [True])
observed_actor.ZoomState.bWantsToZoom = False
observed_manager.mode = "Default"
observed.sync("apex_movement", observed_pc, settings, 33)
check("a persistent Default getter cannot end an observed vehicle session",
      observed._in_vehicle and observed._mode_pushes == 0 and observed_manager.pushes == 1)
observed_path = next(path for path in observed._transitions.paths
                     if path.endswith(":CameraTransition"))
observed_callback = observed.hooks.items[(observed_path, "PRE", "ads_observed_vehicle")]
observed_callback(observed_pc, args("Default"), None, Bound())
observed_manager.mode = "ThirdPerson"
observed.sync("apex_movement", observed_pc, settings, 34)
check("the exit transition rebuilds one complete owned camera unit",
      not observed._in_vehicle and observed._mode_pushes == 1
      and observed_manager.pushes == 2 and observed_bridge.starts == 2
      and observed._suspensions == set())
observed.stop()


class OnceFailingSuspendBridge(Bridge):
    def __init__(self):
        super().__init__()
        self.failures = 1

    def suspend(self, value):
        if self.failures:
            self.failures -= 1
            raise RuntimeError("temporary suspension failure")
        super().suspend(value)


suspend_actor = types.SimpleNamespace(ZoomState=types.SimpleNamespace(bWantsToZoom=False))
suspend_manager, suspend_bridge = Manager(), OnceFailingSuspendBridge()
suspend_pc = player(34, suspend_actor, suspend_manager)
suspend_controller = ThirdPersonController(Hooks(), suspend_bridge, identifier="ads_suspend")
suspend_controller.sync("apex_movement", suspend_pc, settings, 40)
suspend_actor.ZoomState.bWantsToZoom = True
try:
    suspend_controller.sync("apex_movement", suspend_pc, settings, 41)
except RuntimeError:
    pass
check("a refused bridge suspension leaves third person and logical state intact",
      suspend_manager.mode == "ThirdPerson" and suspend_controller._mode_pushes == 1
      and not suspend_controller._aiming and suspend_controller._suspensions == set()
      and not suspend_controller._transitions._first_person_allowed)
suspend_controller.sync("apex_movement", suspend_pc, settings, 42)
check("the next frame can retry the suspension and enter native aim",
      suspend_controller._aiming and suspend_controller._mode_pushes == 0
      and suspend_bridge.suspended == [True])
suspend_controller.stop()


class OnceFailingResumeBridge(Bridge):
    def __init__(self):
        super().__init__()
        self.failed = False

    def suspend(self, value):
        if not value and not self.failed:
            self.failed = True
            raise RuntimeError("temporary resume failure")
        super().suspend(value)


resume_actor = types.SimpleNamespace(ZoomState=types.SimpleNamespace(bWantsToZoom=False))
resume_manager, resume_bridge = Manager(), OnceFailingResumeBridge()
resume_pc = player(35, resume_actor, resume_manager)
resume = ThirdPersonController(Hooks(), resume_bridge, identifier="ads_resume")
resume.sync("apex_movement", resume_pc, settings, 50)
resume_actor.ZoomState.bWantsToZoom = True
resume.sync("apex_movement", resume_pc, settings, 51)
resume_actor.ZoomState.bWantsToZoom = False
resume.sync("apex_movement", resume_pc, settings, 52)
try:
    resume.sync("apex_movement", resume_pc, settings, 53)
except RuntimeError:
    pass
check("a refused bridge resume keeps the confirmed return pending",
      resume._aim_returning and resume._suspensions == {"aim"}
      and resume_bridge.suspended == [True])
resume.sync("apex_movement", resume_pc, settings, 54)
check("the next frame retries and completes the bridge resume",
      not resume._aim_returning and resume._suspensions == set()
      and resume_bridge.suspended == [True, False])
resume.stop()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
