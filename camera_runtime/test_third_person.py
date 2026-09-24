"""Third-person lifecycle follows the live character and rolls partial work back."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.third_person import ThirdPersonController  # noqa: E402
from camera_test_fixtures import Bridge, Hooks, Manager, Settings  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


manager, bridge, hooks = Manager(), Bridge(), Hooks()
actor = object()
pc = types.SimpleNamespace(_get_address=lambda: 10, OakCharacter=actor, PlayerCameraManager=manager)
controller = ThirdPersonController(hooks, bridge, identifier="camera")
settings = Settings()
controller.sync("apex_movement", pc, settings, 1)
check("enabling pushes the validated mode and starts the bridge",
      manager.mode == "ThirdPerson" and manager.pushes == 1 and bridge.starts == 1)
controller.sync("apex_movement", pc, settings, 2)
check("repeated frames do not stack camera modes", manager.pushes == 1 and bridge.starts == 1)
bridge.fail_stop = True
settings.enabled = False
try:
    controller.sync("apex_movement", pc, settings, 3)
except RuntimeError:
    pass
check("a failed native stop leaves cleanup pending", controller.cleanup_pending and manager.pops == 1)
bridge.fail_stop = False
controller.stop()
check("a later cleanup retries only unfinished work", not controller.cleanup_pending and bridge.stops == 2
      and manager.pops == 1)

recovery_manager, recovery_bridge = Manager(), Bridge()
recovery_pc = types.SimpleNamespace(_get_address=lambda: 12, OakCharacter=actor,
                                    PlayerCameraManager=recovery_manager)
recovery_clock = [5]
recovery = ThirdPersonController(Hooks(), recovery_bridge, identifier="recovery",
                                 clock=lambda: recovery_clock[0])
settings.enabled = True
recovery.sync("apex_movement", recovery_pc, settings, 4)
recovery_bridge.fail_stop = True
settings.enabled = False
try:
    recovery.sync("apex_movement", recovery_pc, settings, 5)
except RuntimeError:
    pass
recovery_bridge.fail_stop = False
settings.enabled = True
recovery_clock[0] = 100_000_005
recovery.sync("apex_movement", recovery_pc, settings, recovery_clock[0])
check("re-enabling after partial cleanup rebuilds one complete camera unit",
      recovery_bridge.starts == 2 and recovery_manager.pushes == 2)
recovery.stop()
check("the recovered camera mode is owned and removed on stop", recovery_manager.pops == 2)


class Collision:
    calls = 0

    def sample(self, _now, _world, _bridge, update):
        self.calls += 1
        update(True)


settings.enabled = True
collision = Collision()
guarded = ThirdPersonController(hooks, bridge, identifier="guarded", collision=collision)
guarded.sync("apex_movement", pc, settings, 50_000_000)
check("the collision guard uses the shared suspension state",
      collision.calls == 1 and bridge.suspended[-1] is True)
guarded.stop()

stable_manager, stable_bridge = Manager(), Bridge()
stable_pc = types.SimpleNamespace(_get_address=lambda: 21, OakCharacter=actor,
                                  PlayerCameraManager=stable_manager)
stable_clone = types.SimpleNamespace(_get_address=lambda: 21, OakCharacter=actor,
                                     PlayerCameraManager=stable_manager)
stable = ThirdPersonController(Hooks(), stable_bridge, identifier="stable")
stable.sync("apex_movement", stable_pc, settings, 1)
stable.sync("apex_movement", stable_clone, settings, 2)
check("a fresh SDK wrapper for the same player does not restart the camera",
      stable_bridge.starts == 1 and stable_manager.pushes == 1)
replacement = types.SimpleNamespace(_get_address=lambda: 21, OakCharacter=object(),
                                    PlayerCameraManager=stable_manager)
stable.sync("apex_movement", replacement, settings, 3)
check("a respawn releases the old character and starts the new one",
      stable_bridge.starts == 2 and stable_manager.pushes == 2 and stable_manager.pops == 1)
stable.stop()


class FailingManager(Manager):
    def PushActorCameraMode(self, *_args):
        raise RuntimeError("push failed")


failing_manager, failing_bridge, failing_hooks = FailingManager(), Bridge(), Hooks()
failing_pc = types.SimpleNamespace(_get_address=lambda: 11, OakCharacter=actor,
                                   PlayerCameraManager=failing_manager)
failed = ThirdPersonController(failing_hooks, failing_bridge, identifier="failing")
try:
    failed.sync("apex_movement", failing_pc, settings, 60_000_000)
except RuntimeError:
    pass
check("a partial setup rolls back the bridge and hooks",
      not failed.cleanup_pending and failing_hooks.items == {} and failing_bridge.stops == 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
