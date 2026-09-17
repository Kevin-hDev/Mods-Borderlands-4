"""Tests feeling the wall: the three traces, their start and direction, what they report of the surfaces they met, and
the library looked up once. Judging a surface climbable belongs to climb_rules, so nothing is thrown away here."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import climb_aim, wall_sense  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


kismet = state["kismet"]
player = sdk_stubs.FakeCharacter()
player.location = sdk_stubs.vector(10.0, 20.0, 100.0)

HALF = 90.0

check("nothing in front is no wall at all", wall_sense.walls_ahead(player, 0.0, HALF) == [])
check("one trace per height is fired, from under the feet to over the head",
      [round(call[0].Z) for call in kismet.calls]
      == [round(100 + share * HALF) for share in climb_aim.TRACE_HEIGHTS])
start, end, channel, ignore_self = kismet.calls[2]
check("the middle one starts behind the character, so a wall it touches is still in front of the ray",
      (round(start.X), start.Y, start.Z) == (-50, 20.0, 100.0))
check("and reaches 300 past the character, level", (round(end.X), round(end.Y), end.Z) == (310, 20, 100.0))
check("on the channel that meets these walls, ignoring the character",
      channel == wall_sense.TRACE_CHANNEL == 2 and ignore_self is True)
wall_sense.walls_ahead(player, 90.0, HALF)
check("a camera turned 90 degrees traces along Y", (round(kismet.calls[-1][1].X), round(kismet.calls[-1][1].Y)) == (10, 320))

kismet.hit = (60.0, sdk_stubs.vector(-1.0, 0.0, 0.0))
check("a wall gives its distance from the character, not from where the ray started, once per trace that met it",
      wall_sense.walls_ahead(player, 0.0, HALF)
      == [climb_aim.Wall(distance=0.0, into_x=1.0, into_y=0.0, flat=1.0)] * len(climb_aim.TRACE_HEIGHTS))
kismet.hit = (150.0, sdk_stubs.vector(-1.0, 0.0, 0.0))
check("a wall the ray meets at 150 is 90 from the character", wall_sense.walls_ahead(player, 0.0, HALF)[0].distance == 90.0)
kismet.hit = (60.0, sdk_stubs.vector(-1.0, 0.0, 0.0))
kismet.hits_by_z = {100: (60.0, sdk_stubs.vector(-1.0, 0.0, 0.0))}
check("a face only the middle trace meets still comes back, alone",
      len(wall_sense.walls_ahead(player, 0.0, HALF)) == 1)
kismet.hits_by_z = None
kismet.hit = (60.0, sdk_stubs.vector(-0.6, 0.0, 0.8))
slope = wall_sense.walls_ahead(player, 0.0, HALF)[0]
check("a slope comes back too, with how upright it stands", round(slope.flat, 2) == 0.6)
kismet.hit = (60.0, sdk_stubs.vector(-0.72, 0.0, 0.69))
steep = wall_sense.walls_ahead(player, 0.0, HALF)[0]
check("a steep face gives its way in, made flat and whole", abs(steep.into_x - 1.0) < 1e-9)
kismet.hit = (60.0, sdk_stubs.vector(0.0, 0.0, 1.0))
floor = wall_sense.walls_ahead(player, 0.0, HALF)[0]
check("a floor has no way into it and no uprightness at all",
      (floor.into_x, floor.into_y) == (0.0, 0.0) and floor.flat < 1e-6)

check("the engine library is looked up once, whatever the number of traces", state["class_finds"] == 1)
wall_sense.reset()
wall_sense.walls_ahead(player, 0.0, HALF)
check("after a reset it is looked up again", state["class_finds"] == 2)

# The way up along the surface, measured from the whole normal, not guessed from its flat part.
kismet.hit = (60.0, sdk_stubs.vector(-1.0, 0.0, 0.0))
upright = wall_sense.walls_ahead(player, 0.0, HALF)[0]
check("a wall standing straight gives a straight way up", (upright.up_x, upright.up_y, upright.up_z) == (0.0, 0.0, 1.0))
kismet.hit = (60.0, sdk_stubs.vector(-0.95, 0.0, 0.31))
leaning = wall_sense.walls_ahead(player, 0.0, HALF)[0]
check("a wall leaning back tips the way up into itself",
      round(leaning.up_x, 2) == 0.31 and round(leaning.up_z, 2) == 0.95)
check("and the way up stays one unit long",
      abs((leaning.up_x ** 2 + leaning.up_y ** 2 + leaning.up_z ** 2) - 1.0) < 1e-6)
kismet.hit = (60.0, sdk_stubs.vector(0.0, 0.0, 1.0))
floor_up = wall_sense.walls_ahead(player, 0.0, HALF)[0]
check("a floor keeps a straight way up rather than none at all",
      (floor_up.up_x, floor_up.up_y, floor_up.up_z) == (0.0, 0.0, 1.0))
kismet.hit = (60.0, sdk_stubs.vector(-1.0, 0.0, 0.0))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
