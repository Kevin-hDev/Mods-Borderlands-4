"""The other shoulder is measured as the mirror of the shown one, only when the shoulder state asks; with the
automatic shoulder on, a cramped side is swept again ahead and behind, so a pole is not a wall."""

import math
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.shoulder_auto import CLEAR  # noqa: E402
from apex_camera_runtime.shoulder_clearance import MAX_AGE, SPREAD_CM, ShoulderClearance  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def close(a, b):
    return all(math.isclose(x, y, abs_tol=1e-6) for x, y in zip(a, b))


class Sweep:
    def __init__(self, free=1.0, fail=False):
        self.free, self.fail = free, fail
        self.calls = []

    def distance(self, _actor, anchor, desired):
        self.calls.append((anchor, desired))
        if self.fail:
            raise ValueError("invalid collision contact")
        return math.dist(anchor, desired) * self.free


class Pole(Sweep):
    """A thin pole cuts only the sweeps that start at the anchor's own X: moved ahead or behind, they pass it."""
    def distance(self, actor, anchor, desired):
        free = super().distance(actor, anchor, desired)
        return free if math.isclose(anchor[0], ANCHOR[0]) else math.dist(anchor, desired)


def manager(yaw):
    return types.SimpleNamespace(GetCameraRotation=lambda: types.SimpleNamespace(Yaw=yaw, Pitch=0.0))


ANCHOR = (100.0, 200.0, 50.0)
# Facing +X (yaw 0), the right side is +Y: the right shoulder is 48.4 to +Y, 5 up.
RIGHT = (100.0, 248.4, 55.0)
LENGTH = math.dist(ANCHOR, RIGHT)
CAMERA = (100.0, 214.5, 51.5)

clearance = ShoulderClearance()
sweep = Sweep()
clearance.record(sweep, None, manager(0.0), ANCHOR, RIGHT, LENGTH * 0.3, CAMERA)
reading = clearance.take()
check("the shown side's room comes from the guard's sweep", math.isclose(reading.room, 0.3, rel_tol=1e-6))
check("the shown camera is kept for the view ahead", reading.camera == CAMERA)
check("unless asked, no second sweep", sweep.calls == [] and reading.other_room is None
      and reading.other_camera is None)

clearance.wanted = True
sweep.free = 0.5
clearance.record(sweep, None, manager(0.0), ANCHOR, RIGHT, LENGTH * 0.3, CAMERA)
reading = clearance.take()
check("when asked, the mirror across the right axis is swept", close(sweep.calls[-1][1], (100.0, 151.6, 55.0)))
check("the other side's room is read", math.isclose(reading.other_room, 0.5))
check("the other camera stands as far as its room lets it", close(reading.other_camera, (100.0, 175.8, 52.5)))

clearance.record(sweep, None, manager(90.0), ANCHOR, (51.6, 200.0, 55.0), 48.4, CAMERA)
check("facing +Y, the mirror is found along X", close(sweep.calls[-1][1], (148.4, 200.0, 55.0)))

calls = len(sweep.calls)
clearance.record(sweep, None, manager(0.0), ANCHOR, (100.0, 205.0, 55.0), 2.0, CAMERA)
check("mid-switch, both sides are one point: no second sweep",
      len(sweep.calls) == calls and clearance.take().other_room is None)

for _ in range(MAX_AGE):
    clearance.take()
check("a reading stops counting once the guard stops measuring", clearance.take() is None)
clearance.record(sweep, None, manager(0.0), ANCHOR, RIGHT, LENGTH, CAMERA)
clearance.clear()
check("clearing drops the reading", clearance.take() is None)

failing = Sweep(fail=True)
try:
    clearance.record(failing, None, manager(0.0), ANCHOR, RIGHT, 10.0, CAMERA)
except ValueError:
    raised = True
else:
    raised = False
check("a failed second sweep reaches the guard's own error path", raised)

# Kevin, 2026-10-08: a pole behind the hunter swapped the shoulder; a wall alongside must still.
clearance = ShoulderClearance()
clearance.active = True
pole = Pole(free=0.2)
clearance.record(pole, None, manager(0.0), ANCHOR, RIGHT, LENGTH * 0.2, CAMERA)
reading = clearance.take()
check("a pole cut only by the shown sweep leaves the side roomy", reading.room >= CLEAR)
check("the first extra sweep runs a little ahead, along the camera's view",
      close(pole.calls[0][0], (100.0 + SPREAD_CM, 200.0, 50.0)) and close(pole.calls[0][1], (100.0 + SPREAD_CM, 248.4, 55.0)))
check("once roomy, no further sweep", len(pole.calls) == 1)
check("the camera itself still stops at the pole", reading.camera == CAMERA)
check("without the other side wanted, no mirror sweep", reading.other_room is None)

wall = Sweep(free=0.3)
clearance.record(wall, None, manager(0.0), ANCHOR, RIGHT, LENGTH * 0.3, CAMERA)
reading = clearance.take()
check("a wall alongside cuts all three sweeps: still cramped", math.isclose(reading.room, 0.3))
check("the last extra sweep runs a little behind", close(wall.calls[1][0], (100.0 - SPREAD_CM, 200.0, 50.0)))

roomy = Sweep()
clearance.record(roomy, None, manager(0.0), ANCHOR, RIGHT, LENGTH * CLEAR, CAMERA)
check("a roomy side is not swept again", roomy.calls == [])

clearance.active = False
clearance.record(Pole(free=0.2), None, manager(0.0), ANCHOR, RIGHT, LENGTH * 0.2, CAMERA)
check("with the automatic shoulder off, no extra sweep", math.isclose(clearance.take().room, 0.2))

clearance.active = clearance.wanted = True
mirror_pole = Pole(free=0.4)
clearance.record(mirror_pole, None, manager(0.0), ANCHOR, RIGHT, LENGTH, CAMERA)
reading = clearance.take()
check("a pole on the other side is not a wall either", reading.other_room >= CLEAR)
check("each side says what cut its roomiest sweep, here nothing", reading.seen == "clear"
      and reading.other_seen == "clear")
check("the other camera still stands where its own sweep stops", close(reading.other_camera, (100.0, 180.64, 52.0)))

class Named(Sweep):
    """A wall alongside, named in its contact; moved sweeps can start inside it and fail."""
    def __init__(self, fail_moved=False):
        super().__init__(free=0.3)
        self.fail_moved = fail_moved

    def distance(self, actor, anchor, desired):
        moved = not math.isclose(anchor[0], ANCHOR[0])
        if moved and self.fail_moved:
            self.calls.append((anchor, desired))
            raise ValueError("invalid initial collision depth")
        free = super().distance(actor, anchor, desired)
        self.hit = types.SimpleNamespace(Distance=free, HitObjectHandle=types.SimpleNamespace(
            Actor=types.SimpleNamespace(Name="Moved" if moved else "Shown")))
        return free


clearance = ShoulderClearance()
clearance.active = True
named = Named()
named.hit = types.SimpleNamespace(HitObjectHandle=types.SimpleNamespace(Actor=types.SimpleNamespace(Name="Main")))
clearance.record(named, None, manager(0.0), ANCHOR, RIGHT, LENGTH * 0.3, CAMERA)
check("a wall alongside is named from the guard's own contact", clearance.take().seen.startswith(
    f"{LENGTH * 0.3:.0f} cm on Main/"))
failing = Named(fail_moved=True)
clearance.record(failing, None, manager(0.0), ANCHOR, RIGHT, LENGTH * 0.3, CAMERA)
reading = clearance.take()
check("a moved sweep starting inside the wall proves nothing and stops nothing (2026-10-08 third trial)",
      math.isclose(reading.room, 0.3) and len(failing.calls) == 2)
unnamed = Sweep(free=0.3)
clearance.record(unnamed, None, manager(0.0), ANCHOR, RIGHT, LENGTH * 0.3, CAMERA)
check("without a contact the side still gives its distance", clearance.take().seen == f"{LENGTH * 0.3:.0f} cm")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
