"""A throw born on the crosshair's line near the hand is the hunter's, a grenade's payload is not; the game's launch is
turned to leave the hand for the aimed point at the same speed, a grenade's arc kept, and a point too close or a turn
too large gives nothing."""

import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime import thrown_aim as aim  # noqa: E402
from apex_camera_runtime.camera_motion import view_axes  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(a, b, tolerance=1e-6):
    return all(abs(x - y) < tolerance for x, y in zip(a, b))


def unit(vector):
    length = math.sqrt(sum(part * part for part in vector))
    return tuple(part / length for part in vector)


camera, forward = (0.0, 0.0, 0.0), view_axes(0.0, 0.0)[0]
check("the crosshair's point is along the camera's forward at what its line meets",
      near(aim.target(camera, forward, 1097.0), (1097.0, 0.0, 0.0)))
check("with nothing under the crosshair, far along its line",
      near(aim.target(camera, forward, None), (aim.NOTHING_CM, 0.0, 0.0)))
check("the camera's turn is followed", near(aim.target(camera, view_axes(0.0, 90.0)[0], 500.0), (0.0, 500.0, 0.0)))
depth, off = aim.from_line((178.0, -8.0, 26.0), camera, forward)
check("a point's depth and distance off the line", math.isclose(depth, 178.0) and math.isclose(off, math.hypot(8, 26)))

# Measured on 2026-10-21 (rayons-3.txt, third person): the knife born 178 cm ahead of the camera, 8 cm left and 26 cm
# up; the body's left hand 257 cm ahead, 66 cm right and 21 cm down; the crosshair on a wall 1249 cm away.
spawn, hand, point = (178.0, -8.0, 26.0), (257.0, 66.0, -21.0), (1249.0, 0.0, 0.0)
check("a throw born on the crosshair's line near the hand is the hunter's", aim.born_as_throw(spawn, camera, forward, hand))
check("a payload born at the hunter's feet is not", not aim.born_as_throw((150.0, 60.0, -180.0), camera, forward, hand))
check("nor one born where a grenade burst 20 m away",
      not aim.born_as_throw((2000.0, 0.0, 0.0), camera, forward, hand))
check("nor one behind the camera", not aim.born_as_throw((-40.0, 0.0, 0.0), camera, forward, (-40.0, 30.0, 0.0)))
check("nor one on the line but far from the hand",
      not aim.born_as_throw(spawn, camera, forward, (spawn[0], spawn[1] + aim.MAX_HAND_CM + 1, spawn[2])))

knife = tuple(4000.0 * part for part in unit([p - s for p, s in zip(point, spawn)]))
launch = aim.turned(knife, spawn, hand, point)
check("the knife the game aims at the point leaves the hand for it at the same speed",
      near(launch, tuple(4000.0 * part for part in unit([p - h for p, h in zip(point, hand)]))))
line = unit([p - s for p, s in zip(point, spawn)])
level_up = view_axes(0.0, 0.0)[2]
# The lob is measured from the game's line, so its up is taken square to that line.
up = unit([u - sum(a * b for a, b in zip(level_up, line)) * l for u, l in zip(level_up, line)])
lobbed = tuple(2451.0 * (math.cos(math.radians(20)) * l + math.sin(math.radians(20)) * u) for l, u in zip(line, up))
lifted = aim.turned(lobbed, spawn, hand, point)
check("a grenade lobbed 20 degrees keeps its speed and its lob over the hand's line",
      math.isclose(math.sqrt(sum(v * v for v in lifted)), 2451.0)
      and math.isclose(aim.angle_deg(lifted, [p - h for p, h in zip(point, hand)]), 20.0, abs_tol=1e-6)
      and lifted[2] > 0.0)
check("the turn is the angle between the two lines",
      math.isclose(aim.angle_deg(knife, launch), aim.angle_deg([p - s for p, s in zip(point, spawn)],
                                                                [p - h for p, h in zip(point, hand)])))
check("a point closer to the hand than the minimum gives nothing",
      aim.turned(knife, spawn, hand, (hand[0] + aim.MIN_FLIGHT_CM - 1, hand[1], hand[2])) is None)
check("nor a point closer to the spawn than the minimum",
      aim.turned(knife, spawn, hand, (spawn[0] + aim.MIN_FLIGHT_CM - 1, spawn[1], spawn[2])) is None)
check("a wall 3 m ahead asks a turn over the limit: nothing", aim.turned(knife, spawn, hand, (300.0, 0.0, 0.0)) is None)
check("an object without speed gives nothing", aim.turned((0.0, 0.0, 0.0), spawn, hand, point) is None)
check("a hand on the game's line keeps the launch", near(aim.turned(knife, spawn, spawn, point), knife))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
