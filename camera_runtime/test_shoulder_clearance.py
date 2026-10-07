"""The other shoulder is measured as the mirror of the shown one, only when the shoulder state asks."""

import math
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.shoulder_clearance import MAX_AGE, ShoulderClearance  # noqa: E402

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
        self.reduced = True

    def distance(self, _actor, anchor, desired):
        self.calls.append((anchor, desired))
        self.reduced = False
        if self.fail:
            raise ValueError("invalid collision contact")
        return math.dist(anchor, desired) * self.free


def manager(yaw):
    return types.SimpleNamespace(GetCameraRotation=lambda: types.SimpleNamespace(Yaw=yaw, Pitch=0.0))


ANCHOR = (100.0, 200.0, 50.0)
# Facing +X (yaw 0), the right side is +Y: the right shoulder is 48.4 to +Y, 5 up.
RIGHT = (100.0, 248.4, 55.0)
LENGTH = math.dist(ANCHOR, RIGHT)
CAMERA = (100.0, 214.5, 51.5)

clearance = ShoulderClearance()
sweep = Sweep()
clearance.record(sweep, None, manager(0.0), ANCHOR, RIGHT, LENGTH * 0.3, False, CAMERA)
reading = clearance.take()
check("the shown side's room comes from the wall check", math.isclose(reading.room, 0.3, rel_tol=1e-6))
check("the shown camera is kept for the view ahead", reading.camera == CAMERA)
check("unless asked, no second sweep", sweep.calls == [] and reading.other_room is None
      and reading.other_camera is None)

clearance.wanted = True
sweep.free = 0.5
clearance.record(sweep, None, manager(0.0), ANCHOR, RIGHT, LENGTH * 0.3, False, CAMERA)
reading = clearance.take()
check("when asked, the mirror across the right axis is swept", close(sweep.calls[-1][1], (100.0, 151.6, 55.0)))
check("the other side's room is read", math.isclose(reading.other_room, 0.5))
check("the other camera stands as far as its room lets it", close(reading.other_camera, (100.0, 175.8, 52.5)))
check("the shown side's reduced-volume flag survives the second sweep", sweep.reduced is True)

clearance.record(sweep, None, manager(90.0), ANCHOR, (51.6, 200.0, 55.0), 48.4, False, CAMERA)
check("facing +Y, the mirror is found along X", close(sweep.calls[-1][1], (148.4, 200.0, 55.0)))

calls = len(sweep.calls)
clearance.record(sweep, None, manager(0.0), ANCHOR, (100.0, 205.0, 55.0), 2.0, False, CAMERA)
check("mid-switch, both sides are one point: no second sweep",
      len(sweep.calls) == calls and clearance.take().other_room is None)
clearance.record(sweep, None, manager(0.0), ANCHOR, RIGHT, LENGTH, True, ANCHOR)
check("a wall latch counts as no room at all", clearance.take().room == 0.0)

for _ in range(MAX_AGE):
    clearance.take()
check("a reading stops counting once the wall check stops", clearance.take() is None)
clearance.record(sweep, None, manager(0.0), ANCHOR, RIGHT, LENGTH, False, CAMERA)
clearance.clear()
check("clearing drops the reading", clearance.take() is None)

failing = Sweep(fail=True)
try:
    clearance.record(failing, None, manager(0.0), ANCHOR, RIGHT, 10.0, False, CAMERA)
except ValueError:
    raised = True
else:
    raised = False
check("a failed second sweep reaches the wall check's own error path", raised)
check("a failed second sweep still restores the reduced flag", failing.reduced is True)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
