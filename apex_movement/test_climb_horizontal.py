"""Tests a wall climb that may start and travel fully sideways, with the same budget as a vertical climb."""

import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from apex_movement import climb_aim as aim  # noqa: E402
from apex_movement import climb_rules as rules  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


MS = 1_000_000
WALL = aim.Wall(distance=60.0, into_x=1.0, into_y=0.0, flat=1.0)
LIMITS = rules.Limits(distance=372.0, delay_ns=0, lean_deg=90.0, speed=370.0)
STRAIGHT = rules.Limits(distance=372.0, delay_ns=0, lean_deg=0.0, speed=370.0)


def moment(now_ms: int, angle: float = 90.0, **changes: object) -> rules.Moment:
    radians = math.radians(angle)
    values: dict[str, object] = dict(
        now_ns=now_ms * MS, in_air=True, on_ground=False, game_move=False, mantling=False,
        near_game_climb=False, x=0.0, y=0.0, z=0.0, jumps=1,
        stick_x=math.cos(radians), stick_y=math.sin(radians), view_yaw=angle,
        wall=WALL, hits=5, high_wall=True,
    )
    values.update(changes)
    return rules.Moment(**values)


check("a stick exactly along either side of the wall asks for a 90 degree climb",
      aim.lean_degrees(0.0, 1.0, WALL, 90.0) == 90.0
      and aim.lean_degrees(0.0, -1.0, WALL, 90.0) == -90.0)
check("the configured angle controls starts and active climbs without ever pointing away from the wall",
      aim.start_angle(0.0) == 45.0 and aim.start_angle(90.0) == 90.0 and aim.keep_angle(90.0) == 90.0)
check("with no diagonal a stick 40 degrees off starts and 50 does not",
      rules.Rules().step(moment(0, angle=40.0), STRAIGHT).event == "start"
      and rules.Rules().step(moment(0, angle=50.0), STRAIGHT).event == "")

horizontal = aim.climb_direction(90.0, WALL)
check("a 90 degree climb is fully horizontal and keeps full speed",
      tuple(round(value, 6) for value in horizontal) == (0.0, 1.0, 0.0))

started = rules.Rules()
check("a climb starts while arriving parallel to the wall",
      started.step(moment(0), LIMITS).event == "start")

# Vertical and horizontal movement consume the same 372-unit budget.
vertical = rules.Rules()
vertical.step(moment(0, angle=0.0), LIMITS)
vertical_end = vertical.step(moment(1000, angle=0.0, z=372.0), LIMITS)
check("372 units vertically consume the climb budget",
      vertical_end.event == rules.DISTANCE and vertical_end.distance == 372.0)

sideways = rules.Rules()
sideways.step(moment(0), LIMITS)
check("a horizontal climb is not mistaken for being stuck",
      sideways.step(moment(500, y=185.0), LIMITS).climbing)
sideways_end = sideways.step(moment(1000, y=372.0), LIMITS)
check("372 units horizontally consume the same climb budget",
      sideways_end.event == rules.DISTANCE and sideways_end.rise == 0.0 and sideways_end.distance == 372.0)

diagonal = rules.Rules()
diagonal.step(moment(0, angle=45.0), LIMITS)
distance = 372.0 / math.sqrt(2.0)
diagonal_end = diagonal.step(moment(1000, angle=45.0, y=distance, z=distance), LIMITS)
check("a diagonal consumes distance along the wall rather than vertical height",
      diagonal_end.event == rules.DISTANCE and round(diagonal_end.distance) == 372)

stuck = rules.Rules()
stuck.step(moment(0), LIMITS)
check("no movement for 0.2 seconds is still blocked",
      stuck.step(moment(200), LIMITS).event == rules.BLOCKED)

grace = rules.Rules()
grace.step(moment(0), LIMITS)
grace.step(moment(100, angle=100.0, view_yaw=90.0), LIMITS)
check("a brief stick overshoot beyond 90 degrees keeps the climb",
      grace.step(moment(790, angle=100.0, y=100.0, view_yaw=90.0), LIMITS).climbing)
check("the same overshoot ends the climb after 0.70 seconds",
      grace.step(moment(800, angle=100.0, y=101.0, view_yaw=90.0), LIMITS).event == rules.STICK)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
