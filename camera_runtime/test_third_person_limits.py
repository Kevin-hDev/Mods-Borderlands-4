"""Cleanup, recovery pushes and camera-manager ownership stay bounded."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.third_person import ThirdPersonController  # noqa: E402
from camera_test_fixtures import Bridge, Hooks, Manager, Settings  # noqa: E402

fails = []


def check(label, condition):
    print(("OK    " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def pc(address, actor, manager):
    return types.SimpleNamespace(_get_address=lambda: address, OakCharacter=actor,
                                 PlayerCameraManager=manager)


settings = Settings()
settings.enabled = True

# An exhausted old unit may be abandoned on a genuinely new player/map.
clock = [1_000_000_000]
blocked_bridge, blocked_manager = Bridge(), Manager()
old_actor = object()
blocked = ThirdPersonController(Hooks(), blocked_bridge, "blocked", clock=lambda: clock[0])
blocked.sync("apex", pc(1, old_actor, blocked_manager), settings, clock[0])
blocked_bridge.fail_stop = True
settings.enabled = False
try:
    blocked.sync("apex", pc(1, old_actor, blocked_manager), settings, clock[0])
except RuntimeError:
    pass
for due in (1_100_000_000, 1_300_000_000, 1_700_000_000):
    clock[0] = due
    blocked.sync("apex", pc(1, old_actor, blocked_manager), settings, due)
blocked_bridge.fail_stop = False
settings.enabled = True
blocked.sync("apex", pc(2, object(), Manager()), settings, 2_000_000_000)
check("a new map resets an exhausted stale cleanup and starts a fresh unit",
      blocked_bridge.starts == 2)

# A persistent stale bridge failure gets one initial attempt, then three shared retries.
retry_bridge = Bridge()
retry = ThirdPersonController(Hooks(), retry_bridge, "identity", clock=lambda: clock[0])
first_pc = pc(10, object(), Manager())
retry.sync("apex", first_pc, settings, 3_000_000_000)
retry_bridge.fail_stop = True
new_pc = pc(11, object(), Manager())
for due in (3_000_000_001, 3_100_000_001, 3_300_000_001, 3_700_000_001):
    clock[0] = due
    try:
        retry.sync("apex", new_pc, settings, due)
    except RuntimeError:
        pass
for frame in range(1_200):
    clock[0] += 16_666_667
    try:
        retry.sync("apex", new_pc, settings, clock[0])
    except RuntimeError:
        pass
check("one identity stops cleanup after three delayed retries", retry_bridge.stops == 4)

# Turning the option off gets one final attempt after the automatic budget is exhausted.
retry.sync("apex", None, settings, clock[0] + 1)
check("a missing player does not consume the manual-disable attempt", retry_bridge.stops == 4)
retry_bridge.fail_stop = False
settings.enabled = False
retry.sync("apex", new_pc, settings, clock[0] + 2)
for frame in range(60):
    retry.sync("apex", new_pc, settings, clock[0] + 3 + frame)
check("manual disable gets one final bounded cleanup attempt",
      retry_bridge.stops == 5 and not retry.cleanup_pending)
settings.enabled = True


class StickyDefault(Manager):
    def PushActorCameraMode(self, _actor, _mode, *_args):
        self.pushes += 1

    def GetActorCameraMode(self, _actor):
        return "Default"


sticky_manager = StickyDefault()
sticky = ThirdPersonController(Hooks(), Bridge(), "sticky")
sticky_pc = pc(20, object(), sticky_manager)
for frame in range(601):
    sticky.sync("apex", sticky_pc, settings, frame)
check("one owned unit requests at most one recovery push while Default persists",
      sticky_manager.pushes == 2)

# The manager follows the same weak lifetime rule as the player and actor.
slots = {}


def weak(item):
    slot = [item]
    slots[id(item)] = slot
    return lambda: slot[0]


manager_one, manager_two = Manager(), Manager()
manager_pc = pc(30, object(), manager_one)
manager_bridge = Bridge()
managed = ThirdPersonController(Hooks(), manager_bridge, "manager", weak_ref=weak)
managed.sync("apex", manager_pc, settings, 0)
manager_slot = slots.get(id(manager_one))
check("the camera manager is retained through the weak-pointer authority", manager_slot is not None)
if manager_slot is not None:
    manager_slot[0] = None
manager_pc.PlayerCameraManager = manager_two
managed.sync("apex", manager_pc, settings, 1)
check("a replaced camera manager starts one fresh weakly-owned unit",
      manager_slot is not None and manager_bridge.starts == 2 and manager_two.pushes == 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
raise SystemExit(1 if fails else 0)
