"""Vehicle and failed-cleanup recovery remain bounded."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.third_person import MAX_CLEANUP_ATTEMPTS, ThirdPersonController  # noqa: E402
from camera_test_fixtures import Bound, Bridge, Hooks, Manager, Settings, args  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


settings = Settings()
vehicle_manager, vehicle_bridge, vehicle_hooks = Manager(), Bridge(), Hooks()
vehicle_pc = types.SimpleNamespace(_get_address=lambda: 22, OakCharacter=object(),
                                   PlayerCameraManager=vehicle_manager)
vehicle = ThirdPersonController(vehicle_hooks, vehicle_bridge, identifier="vehicle")
vehicle.sync("apex_movement", vehicle_pc, settings, 10)
server_path = next(path for path in vehicle._transitions.paths
                   if path.endswith(":ServerCameraTransition"))
callback = vehicle_hooks.items[(server_path, "PRE", "vehicle")]
callback(vehicle_pc, args("ThirdPersonVehicle"), None, Bound())
vehicle_manager.mode = "Default"
pushes_before = vehicle_manager.pushes
riding_pc = types.SimpleNamespace(_get_address=lambda: 22, OakCharacter=None,
                                  PlayerCameraManager=vehicle_manager)
vehicle.sync("apex_movement", riding_pc, settings, 11)
check("a vehicle may temporarily remove OakCharacter without dismantling the camera owner",
      vehicle.cleanup_pending and vehicle_manager.pops == 0)
vehicle.sync("apex_movement", vehicle_pc, settings, 12)
check("persistent Default during driving never replaces the vehicle camera",
      vehicle_manager.pushes == pushes_before and vehicle_bridge.suspended[-1] is True)
callback(vehicle_pc, args("Default"), None, Bound())
check("vehicle exit waits for native ThirdPerson before resuming",
      vehicle_bridge.suspended[-1] is True)
vehicle_manager.mode = "ThirdPerson"
vehicle.sync("apex_movement", vehicle_pc, settings, 13)
check("the bridge resumes once the on-foot mode is confirmed",
      vehicle_bridge.suspended[-1] is False)
vehicle.stop()


class OnceFailingPopManager(Manager):
    failures = 1

    def PopActorCameraMode(self, actor, *args):
        if self.failures:
            self.failures -= 1
            raise RuntimeError("temporary pop failure")
        return super().PopActorCameraMode(actor, *args)


cleanup_manager, cleanup_bridge, cleanup_hooks = OnceFailingPopManager(), Bridge(), Hooks()
cleanup_pc = types.SimpleNamespace(_get_address=lambda: 23, OakCharacter=object(),
                                   PlayerCameraManager=cleanup_manager)
cleanup = ThirdPersonController(cleanup_hooks, cleanup_bridge, identifier="cleanup")
cleanup.sync("apex_movement", cleanup_pc, settings, 20)
settings.enabled = False
try:
    cleanup.sync("apex_movement", cleanup_pc, settings, 21)
except RuntimeError:
    pass
cleanup_key = next((key for key in cleanup_hooks.items if key[2] == "cleanup:cleanup"), None)
check("a transient disable failure schedules independent cleanup",
      cleanup_key is not None and cleanup.cleanup_pending)
if cleanup_key is not None:
    cleanup_hooks.items[cleanup_key](object(), None, None, None)
check("the cleanup worker removes the mode after the mod hook is disabled",
      not cleanup.cleanup_pending and cleanup_manager.mode == "Default"
      and not any(key[2] == "cleanup:cleanup" for key in cleanup_hooks.items))
settings.enabled = True


class StaleManager(Manager):
    def __init__(self, stale_actor):
        super().__init__()
        self.stale_actor = stale_actor

    def PopActorCameraMode(self, actor, *_args):
        if actor is self.stale_actor:
            raise RuntimeError("old map is gone")
        return super().PopActorCameraMode(actor, *_args)


stale_actor, fresh_actor = object(), object()
stale_manager, stale_bridge = StaleManager(stale_actor), Bridge()
stale_pc = types.SimpleNamespace(_get_address=lambda: 24, OakCharacter=stale_actor,
                                 PlayerCameraManager=stale_manager)
stale = ThirdPersonController(Hooks(), stale_bridge, identifier="stale")
stale.sync("apex_movement", stale_pc, settings, 30)
fresh_pc = types.SimpleNamespace(_get_address=lambda: 24, OakCharacter=fresh_actor,
                                 PlayerCameraManager=stale_manager)
stale.sync("apex_movement", fresh_pc, settings, 31)
check("a stale mode that cannot be popped does not block the new map",
      stale_bridge.starts == 2 and stale_manager.pushes == 2)
stale.stop()


clock = [1_000_000_000]
retry_manager, retry_bridge, retry_hooks = Manager(), Bridge(), Hooks()
retry_pc = types.SimpleNamespace(_get_address=lambda: 25, OakCharacter=object(),
                                 PlayerCameraManager=retry_manager)
retry = ThirdPersonController(retry_hooks, retry_bridge, identifier="retry",
                              clock=lambda: clock[0])
settings.enabled = True
retry.sync("apex_movement", retry_pc, settings, clock[0])
retry_bridge.fail_stop = True
settings.enabled = False
try:
    retry.sync("apex_movement", retry_pc, settings, clock[0])
except RuntimeError:
    pass
stops_after_failure = retry_bridge.stops
for _ in range(20):
    try:
        retry.sync("apex_movement", retry_pc, settings, clock[0])
    except RuntimeError:
        pass
check("cleanup retries share one backoff instead of running on every animation",
      retry_bridge.stops == stops_after_failure)
settings.enabled = True
for _ in range(20):
    retry.sync("apex_movement", retry_pc, settings, clock[0])
check("an enabled successor also waits for the shared cleanup backoff",
      retry_bridge.stops == stops_after_failure)
settings.enabled = False
cleanup_key = next(key for key in retry_hooks.items if key[2] == "retry:cleanup")
for due in (1_100_000_000, 1_300_000_000, 1_700_000_000):
    clock[0] = due
    retry_hooks.items[cleanup_key](object(), None, None, None)
bounded_stops = retry_bridge.stops
for now in range(2_000_000_000, 3_000_000_000, 100_000_000):
    retry.sync("apex_movement", retry_pc, settings, now)
check("manual disable adds only one final attempt after the automatic retry limit",
      retry_bridge.stops == bounded_stops + 1
      and retry._cleanup_attempts == MAX_CLEANUP_ATTEMPTS)
settings.enabled = True
for now in range(3_000_000_000, 4_000_000_000, 100_000_000):
    try:
        retry.sync("apex_movement", retry_pc, settings, now)
    except RuntimeError:
        pass
check("re-enabling cannot bypass an exhausted cleanup limit",
      retry_bridge.stops == bounded_stops + 1)

stack_manager, stack_bridge = Manager(), Bridge()
stack_pc = types.SimpleNamespace(_get_address=lambda: 26, OakCharacter=object(),
                                 PlayerCameraManager=stack_manager)
stack = ThirdPersonController(Hooks(), stack_bridge, identifier="stack")
settings.enabled = True
stack.sync("apex_movement", stack_pc, settings, 40)
for now in (41, 42, 43):
    stack_manager.mode = "Default"
    stack.sync("apex_movement", stack_pc, settings, now)
stack.stop()
check("every recovery mode push is balanced during cleanup",
      stack_manager.pushes == stack_manager.pops == 2)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
