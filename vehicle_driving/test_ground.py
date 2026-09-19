"""Tests the ground trace: where it starts and ends, what it ignores, a hit, a miss, one class lookup."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


state = sdk_stubs.install()

from vehicle_driving import ground  # noqa: E402

car = sdk_stubs.Vehicle()
check("ground under the vehicle", ground.on_ground(car) is True)
context, start, end, channel, ignore_self, tail = state["ground"].calls[-1]
check("straight down from above the vehicle's origin, with Apex Movement's channel, the vehicle ignored",
      context is car and start.Z == 22.0 + ground.TRACE_UP and end.Z == 22.0 - ground.GROUND_REACH
      and start.X == end.X == 100.0 and start.Y == end.Y == 200.0 and channel == 2 and ignore_self is True
      and tail == 3)
state["ground"].below = None
check("nothing under it: in the air", ground.on_ground(car) is False)
state["ground"].below = ground.TRACE_UP + ground.GROUND_REACH + 1.0
check("ground beyond the reach counts as none", ground.on_ground(car) is False)
check("the trace's class is looked up once", state["class_finds"] == 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
