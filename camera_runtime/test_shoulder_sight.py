"""Each shoulder looks straight ahead along three level lines on the Camera channel, looks again a little higher where a
line is stopped, counts its farthest line, and refuses a result it cannot trust."""

import math
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.shoulder_auto import BLOCKED, CLEAR  # noqa: E402
from apex_camera_runtime.shoulder_sight import (BLOCKED_CM, CAMERA_CHANNEL, CLEAR_CM, MAX_NAME,  # noqa: E402
                                                 OPENING_CM, RISE_CM, SIGHT_CM, SPREAD_CM, ShoulderSight, free_share)

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Sdk:
    @staticmethod
    def make_struct(name, **fields):
        return types.SimpleNamespace(name=name, **fields)


class Kismet:
    """A made-up scene: rule(start, detailed) gives one trace's answer from where the line starts (x, y, z): a distance,
    a hit, None for nothing, or a raw answer."""
    def __init__(self, rule):
        self.rule = rule
        self.calls = []

    def SphereTraceSingle(self, *args):
        self.calls.append(args)
        first = args[1]
        hit = self.rule((first.X, first.Y, first.Z), args[5])
        if isinstance(hit, tuple):
            return hit
        if hit is None:
            return False, Sdk.make_struct("HitResult")
        if isinstance(hit, types.SimpleNamespace):
            return True, hit
        return True, Sdk.make_struct("HitResult", Distance=hit)


def scene(lines=None, low_only=None):
    """What each line meets, by its side offset (0, +SPREAD_CM, -SPREAD_CM); low_only is met only at the camera's
    height, as a step of the floor is."""
    lines, low_only = lines or {}, low_only or {}

    def rule(start, _detailed):
        offset = round(start[1])
        if start[2] > 1e-6:
            return lines.get(offset)
        return low_only.get(offset, lines.get(offset))
    return rule


def share(rule, yaw=0.0):
    kismet = Kismet(rule)
    sight = ShoulderSight(kismet, Sdk())
    return sight.share(actor, (0.0, 0.0, 0.0), yaw), kismet, sight


actor = object()
WALL = {0: 200.0, SPREAD_CM: 200.0, -SPREAD_CM: 200.0}

value, kismet, _sight = share(scene())
check("nothing ahead is fully clear", value == 1.0)
first, last = kismet.calls[0][1], kismet.calls[0][2]
check("the line starts at the camera", (first.X, first.Y, first.Z) == (0.0, 0.0, 0.0))
check("the line goes straight ahead and level", math.isclose(last.X, SIGHT_CM) and last.Y == 0.0 and last.Z == 0.0)
check("the Camera channel is used, so characters are not walls", kismet.calls[0][4] == CAMERA_CHANNEL)
check("the hunter is ignored", kismet.calls[0][6] == [actor])
check("simple then detailed geometry", [call[5] for call in kismet.calls] == [False, True])
check("a clear middle line traces nothing else", len(kismet.calls) == 2)

_value, kismet, _sight = share(scene(), 90.0)
last = kismet.calls[0][2]
check("the camera's yaw turns the line", abs(last.X) < 1e-6 and math.isclose(last.Y, SIGHT_CM))

value, kismet, _sight = share(scene(WALL))
check("a wall across the three lines blocks the view", math.isclose(value, free_share(200.0)))
starts = [(call[1].X, call[1].Y, call[1].Z) for call in kismet.calls[::2]]
check("each line at the camera's height, then a little higher; the middle one first, then either side",
      starts == [(0.0, 0.0, 0.0), (0.0, 0.0, RISE_CM), (0.0, SPREAD_CM, 0.0), (0.0, SPREAD_CM, RISE_CM),
                 (0.0, -SPREAD_CM, 0.0), (0.0, -SPREAD_CM, RISE_CM)])
check("the lines stay level and parallel", all(math.isclose(call[2].X, SIGHT_CM) and call[2].Z == call[1].Z
                                               and call[2].Y == call[1].Y for call in kismet.calls))

value, _kismet, _sight = share(lambda start, detailed: 200.0 if detailed else 600.0)
check("on each line the nearest of its two traces counts", math.isclose(value, free_share(200.0)))
value, _kismet, _sight = share(scene({0: 200.0}))
check("a pillar on the middle line alone leaves the view clear (Kevin, 2026-10-08)", value == 1.0)
value, _kismet, _sight = share(scene({SPREAD_CM: 200.0}))
check("a pillar on a side line alone leaves the view clear", value == 1.0)
value, _kismet, _sight = share(scene(low_only=WALL))
check("a step of the floor across the three lines leaves the view clear (Kevin, 2026-10-08)", value == 1.0)
value, _kismet, _sight = share(scene({0: 400.0, SPREAD_CM: 400.0, -SPREAD_CM: 400.0}, low_only=WALL))
check("a line counts as far as its higher look sees", math.isclose(value, free_share(400.0)))
value, _kismet, _sight = share(scene({0: 200.0, SPREAD_CM: 600.0, -SPREAD_CM: 300.0}))
check("the farthest line counts", math.isclose(value, free_share(600.0)))
value, kismet, _sight = share(scene({0: 200.0, SPREAD_CM: 750.0}))
check("past the clear distance nothing more is traced",
      value > CLEAR and not any(call[1].Y < 0 for call in kismet.calls)
      and not any(call[1].Y > 0 and call[1].Z > 0 for call in kismet.calls))

check("a wall at the swap distance is exactly the swap threshold", math.isclose(free_share(BLOCKED_CM), BLOCKED))
check("a wall at the clear distance is exactly the clear threshold", math.isclose(free_share(CLEAR_CM), CLEAR))
check("about 2.5 m ahead of a hunter 2.6 m in front of the camera is in the way",
      free_share(500.0) < BLOCKED < free_share(520.0))
check("the share grows with the distance", all(free_share(a) < free_share(b) for a, b in
                                               ((0, 100), (300, 510), (510, 600), (720, 790))))
check("the end of the line is fully clear", free_share(SIGHT_CM) == 1.0 and free_share(0.0) == 0.0)
value, _kismet, _sight = share(scene({0: 0.0, SPREAD_CM: 0.0, -SPREAD_CM: 0.0}))
check("a wall at the camera leaves no view", value == 0)

# What the farthest line met, written with a swap: an upright post told from a floor.
post = Sdk.make_struct("HitResult", Distance=450.0, HitObjectHandle=types.SimpleNamespace(
    Actor=types.SimpleNamespace(Name="Bridge_01")), Component=types.SimpleNamespace(
    StaticMesh=types.SimpleNamespace(Name="SM_Post")), ImpactNormal=types.SimpleNamespace(Z=0.004))
_value, _kismet, sight = share(scene({0: 300.0, SPREAD_CM: post, -SPREAD_CM: 400.0}))
check("the swap names what the farthest line met", sight.seen == "450 cm on Bridge_01/SM_Post up 0.00")
_value, _kismet, sight = share(scene({0: 600.0, SPREAD_CM: 600.0, -SPREAD_CM: 600.0}))
check("a hit without names still gives its distance", sight.seen == "600 cm on ?/? up ?")
sight.kismet.rule = scene()
sight.share(actor, (0, 0, 0), 0.0)
check("a clear line says so", sight.seen == "clear")
long = Sdk.make_struct("HitResult", Distance=1.0, HitObjectHandle=types.SimpleNamespace(
    Actor=types.SimpleNamespace(Name="A" * 300)))
_value, _kismet, sight = share(scene({0: long, SPREAD_CM: long, -SPREAD_CM: long}))
check("a long name is cut", sight.seen == f"1 cm on {'A' * MAX_NAME}/? up ?")

# The opening line: past the other camera, away from the shown one (Kevin, 2026-10-08: a door's edge swapped).
SHOWN_CAMERA, OTHER_CAMERA = (0.0, 61.5, 30.0), (0.0, -61.5, 30.0)


def opening(rule, shown=SHOWN_CAMERA, other=OTHER_CAMERA, yaw=0.0):
    kismet = Kismet(rule)
    sight = ShoulderSight(kismet, Sdk())
    return sight.opening(actor, shown, other, yaw), kismet, sight


value, kismet, sight = opening(lambda start, detailed: None)
first, last = kismet.calls[0][1], kismet.calls[0][2]
check("nothing past the other camera is fully clear", value == 1.0 and sight.seen == "clear")
check("the opening line stands past the other camera, at its height",
      (first.X, first.Y, first.Z) == (0.0, -61.5 - OPENING_CM, 30.0))
check("the opening line goes straight ahead and level",
      math.isclose(last.X, SIGHT_CM) and last.Y == first.Y and last.Z == first.Z)
check("a clear opening line is one line in each geometry", len(kismet.calls) == 2)
_value, kismet, _sight = opening(lambda start, detailed: None, OTHER_CAMERA, SHOWN_CAMERA)
check("from the left shoulder the line stands past the right one", kismet.calls[0][1].Y == 61.5 + OPENING_CM)
_value, kismet, _sight = opening(lambda start, detailed: None, (61.5, 0.0, 0.0), (-61.5, 0.0, 0.0), 90.0)
first, last = kismet.calls[0][1], kismet.calls[0][2]
check("the camera's yaw turns the opening line", math.isclose(first.X, -61.5 - OPENING_CM) and abs(first.Y) < 1e-6
      and math.isclose(last.X, first.X) and math.isclose(last.Y, SIGHT_CM))

value, _kismet, sight = opening(lambda start, detailed: 440.0 if start[1] < -100 else None)
check("the wall beside a door blocks the opening line", math.isclose(value, free_share(440.0)) and value < CLEAR
      and sight.seen == "440 cm on ?/? up ?")
value, _kismet, _sight = opening(lambda start, detailed: 440.0 if start[2] < RISE_CM else None)
check("a step of the floor past the other camera does not count as a wall", value == 1.0)

for label, answer in (("a malformed answer", ("hit",)), ("a distance past the line", 900.0),
                      ("an undefined distance", float("nan"))):
    try:
        share(lambda start, detailed, answer=answer: answer)
    except ValueError:
        refused = True
    else:
        refused = False
    check(f"{label} is refused", refused)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
