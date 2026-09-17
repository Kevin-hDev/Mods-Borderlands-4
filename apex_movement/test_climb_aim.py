"""Tests aiming a climb: the angles to a wall, how far the stick leans along it, the direction that comes out of that,
and the longest a climb can last."""

import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from apex_movement import climb_aim as aim  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


WALL = aim.Wall(distance=60.0, into_x=1.0, into_y=0.0, flat=1.0)


def turned(degrees: float) -> dict:
    return {"stick_x": math.cos(math.radians(degrees)), "stick_y": math.sin(math.radians(degrees))}


check("straight into the wall is 0 degrees", aim.angle_to_wall(1.0, 0.0, WALL) == 0.0)
check("along the wall is 90, away from it 180",
      round(aim.angle_to_wall(0.0, 1.0, WALL)) == 90 and round(aim.angle_to_wall(-1.0, 0.0, WALL)) == 180)
check("no stick counts as turned away", aim.angle_to_wall(0.0, 0.0, WALL) == 180.0)
check("the camera is compared the same way, and no camera counts as turned away",
      round(aim.view_angle(90.0, WALL)) == 90 and aim.view_angle(None, WALL) == 180.0)


# The diagonal: how far the stick leans along the wall, and the direction that comes out of it.
def lean(degrees: float, limit: float = 60.0) -> float:
    side = turned(degrees)
    return aim.lean_degrees(side["stick_x"], side["stick_y"], WALL, limit)


check("a stick into the wall leans nothing", lean(0.0) == 0.0)
check("a stick 30 degrees to one side leans 30, and 30 the other way leans -30",
      round(lean(30.0)) == 30 and round(lean(-30.0)) == -30)
check("a stick past the limit leans no further than it", lean(80.0) == 60.0 and lean(-80.0) == -60.0)
check("no lean allowed keeps every stick straight up", lean(50.0, 0.0) == 0.0)
check("no stick at all leans nothing", aim.lean_degrees(0.0, 0.0, WALL, 60.0) == 0.0)

up = aim.climb_direction(0.0, WALL)
check("no lean climbs straight up", (round(up[0], 6), round(up[1], 6), round(up[2], 6)) == (0.0, 0.0, 1.0))
half = aim.climb_direction(60.0, WALL)
check("the fullest diagonal shares the speed: half up, the rest along the wall",
      round(half[2], 3) == 0.5 and round(math.hypot(half[0], half[1]), 3) == 0.866)
check("it goes along the wall, not into it or away from it", round(half[0] * WALL.into_x + half[1] * WALL.into_y, 6) == 0.0)
check("the two sides go opposite ways", round(aim.climb_direction(-60.0, WALL)[1], 6) == -round(half[1], 6))
check("a direction is always a full speed", all(round(math.sqrt(sum(c * c for c in aim.climb_direction(d, WALL))), 6) == 1.0
                                                for d in (-60.0, -17.0, 0.0, 23.0, 60.0)))

check("the longest climb is the fullest diagonal, twice the straight one at 60 degrees",
      round(aim.longest_climb_s(372.0, 370.0, 0.0), 3) == 1.005
      and round(aim.longest_climb_s(372.0, 370.0, 60.0), 3) == 2.011)

# A wall that leans back: the climb follows its face instead of drifting away from it.
LEANING = aim.Wall(distance=60.0, into_x=1.0, into_y=0.0, flat=0.95, up_x=0.31, up_y=0.0, up_z=0.95)

straight = aim.climb_direction(0.0, LEANING)
check("with no lean, a climb goes up along the face, moving into the wall as it rises",
      (round(straight[0], 2), round(straight[1], 2), round(straight[2], 2)) == (0.31, 0.0, 0.95))
tipped = aim.climb_direction(60.0, LEANING)
check("with a diagonal, half of it follows the face and the rest goes along the wall",
      (round(tipped[0], 3), round(tipped[1], 3), round(tipped[2], 3)) == (0.155, 0.866, 0.475))
check("a wall standing straight still climbs straight up",
      aim.climb_direction(0.0, WALL) == (0.0, 0.0, 1.0))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
