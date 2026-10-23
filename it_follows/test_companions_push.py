"""Tests trial 168's push (push.py): the bearing from the hunter to the companion; the place at an aim and a
radius, at the hunter's height; a push begun on the companion's own side turned by its rank's step, ended; each step
a flat push of length one toward the place, forced, with Vex's parameters; none once on the place; the first push of
a walk said before it is made, the next ones not; pushes counted; a failing call raises."""

import math
import pathlib
import sys
import types
from importlib import util

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
sys.modules["unrealsdk"].make_struct = lambda name, **fields: types.SimpleNamespace(struct=name, **fields)
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


spec = util.spec_from_file_location("follow_push_under_test", HERE / "it_follows" / "companions" / "push.py")
push_module = util.module_from_spec(spec)
spec.loader.exec_module(push_module)
events: list[str] = []


class Companion:
    def __init__(self) -> None:
        self.inputs: list = []
        self.broken = False

    def AddMovementInput(self, WorldDirection: object, ScaleValue: float, bForce: bool) -> None:
        if self.broken:
            raise RuntimeError("refused")
        events.append("push")
        self.inputs.append((WorldDirection, ScaleValue, bForce))


check("Vex's push period", push_module.PUSH_S == 0.008)
check("the bearing from the hunter to the companion", math.isclose(push_module.bearing((0, 0, 0), (0, 500, 0)), 90.0)
      and math.isclose(push_module.bearing((100, 100, 0), (-100, 100, 0)), 180.0))
place = push_module.spot((1000.0, 0.0, 250.0), 90.0, 10.0)
check("the place at an aim and a radius, at the hunter's height", math.isclose(place[0], 1000.0, abs_tol=1e-6)
      and math.isclose(place[1], 1000.0) and place[2] == 250.0)

companion = Companion()
pusher = push_module.Push(lambda: companion, "Frame_1", lambda text: events.append(f"note {text}"))
check("not active before a walk", not pusher.active)
pusher.begin((0.0, 0.0, 0.0), (-2000.0, 0.0, 0.0), 22.5)
check("begun on its own side, turned by its rank's step", pusher.active and math.isclose(pusher.aim, 202.5))
pusher.step((0.0, 0.0, 0.0), (-2000.0, 0.0, 0.0), 10.0)
direction, scale, forced = companion.inputs[0]
target = push_module.spot((0.0, 0.0, 0.0), 202.5, 10.0)
expected = (target[0] + 2000.0, target[1])
length = math.hypot(*expected)
check("a flat push of length one toward its place", math.isclose(direction.X, expected[0] / length)
      and math.isclose(direction.Y, expected[1] / length) and direction.Z == 0.0
      and math.isclose(math.hypot(direction.X, direction.Y), 1.0))
check("forced, at full scale, as Vex pushes", scale == 1.0 and forced is True and direction.struct == "Vector")
check("the first push said before it is made", events == [
      "note about to call AddMovementInput on Frame_1, toward its place at 202 degrees", "push"])
pusher.step((0.0, 0.0, 0.0), (-1900.0, 0.0, 0.0), 10.0)
check("the next ones not said", events[-1] == "push" and len(events) == 3 and pusher.pushes == 2)
pusher.step((0.0, 0.0, 0.0), target, 10.0)
check("on its place: no push", pusher.pushes == 2 and len(companion.inputs) == 2)
pusher.end()
check("ended", not pusher.active)
pusher.begin((0.0, 0.0, 0.0), (0.0, 3000.0, 0.0), 0.0)
pusher.step((0.0, 0.0, 0.0), (0.0, 3000.0, 0.0), 10.0)
check("a new walk said again", events[-2].endswith("toward its place at 90 degrees"))
companion.broken = True
try:
    pusher.step((0.0, 0.0, 0.0), (0.0, 2500.0, 0.0), 10.0)
    raised = False
except RuntimeError:
    raised = True
check("a failing call raises", raised)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
