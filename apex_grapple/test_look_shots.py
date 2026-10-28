"""Tests look_shots.py with the game replaced by fakes: two ropes and two hooks built for the settings in use; a shot
that flies, bites and comes back, its rope hanging as rope_motion says and its hook at the rope's end; a new shot while
the last one comes back, and a third; pieces built again for new settings only once no shot is in progress; a new
character's pieces built anew, the old ones never called; our container missing."""

import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import look_assets, look_load, look_settings, look_shots, look_timing, rope_motion  # noqa: E402
from apex_grapple import look_hook  # noqa: E402
import look_fixture  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(a, b, within=1e-6):
    return all(abs(x - y) <= within for x, y in zip(a, b))


S = look_timing.NS_PER_S
HAND, ANCHOR = (0.0, 0.0, 100.0), (2000.0, 0.0, 100.0)
record = look_fixture.install(state)
character = look_fixture.dress(sdk_stubs.FakeCharacter(), record)

look_shots.prepare(character)
places = look_shots._places
check("two ropes of 69 pieces and two hooks, built at the settings in use, and said",
      len(places) == 2 and len(record["pieces"]) == 2 * (69 + 1) and look_shots.built() and not look_shots.busy()
      and any("grapple gun built: rope A at L, 69 pieces a rope, 2 ropes and hooks" in line for line in state["misc"]))
look_shots.prepare(character)
check("nothing built again while the settings stay", len(record["pieces"]) == 140)

shot = look_shots.start(character, HAND, ANCHOR, 1 * S, 0.4)
first = places[0]
check("a shot takes the first place, its light at the player's strength",
      first.shot is shot and places[1].shot is None and look_shots.busy()
      and [args[1] for args in first.rope.material.called("SetScalarParameterValueByInfo")] == [12.0] * 3)

look_shots.tick(character, HAND, int(1.2 * S))
base, way, phase, since = look_timing.where(first.shot, HAND, int(1.2 * S))
expected = rope_motion.laid(rope_motion.shape(HAND, base, "H", 1.0, 0.2), 45.6 * 1.2)
pieces = first.rope.strands[0][0]
hook_at = first.hook.made.called("K2_SetWorldLocationAndRotation")[-1][0]
hook_size = first.hook.made.called("SetWorldScale3D")[-1][0]
check("halfway through the flight, the rope hangs from the hand to the hook's base as the formula says",
      phase == look_timing.OUT and look_fixture.shown(pieces) == len(expected)
      and all(near(look_fixture.put_at(made), start, 1e-3) for made, (start, _) in zip(pieces, expected)))
check("and the hook is at the rope's end, at size B", near((hook_at.X, hook_at.Y, hook_at.Z), base)
      and near((hook_size.X, hook_size.Y, hook_size.Z), (1.4, 1.4, 1.4)))

look_shots.hold(HAND, int(1.4 * S))
look_shots.tick(character, (300.0, 200.0, 150.0), int(1.5 * S))
planted = first.hook.made.called("K2_SetWorldLocationAndRotation")[-1][0]
tip = tuple(b + w * look_hook.length("B") for b, w in zip((planted.X, planted.Y, planted.Z), (1.0, 0.0, 0.0)))
check("caught: the hook stays planted, its point sunk 1.5 cm, wherever the hand goes",
      near(tip, (ANCHOR[0] + look_assets.HOOK_SUNK_CM, 0.0, 100.0), 1e-3))

look_shots.let_go(shot, int(2.0 * S))
look_shots.tick(character, HAND, int(2.1 * S))
back = first.hook.made.called("K2_SetWorldLocationAndRotation")[-1][0]
check("let go, it comes back toward the hand at the hook's speed",
      abs(math.dist(HAND, (back.X, back.Y, back.Z)) - (2000.0 + 1.5 - look_hook.length("B") - 500.0)) < 1e-3)
look_shots.tick(character, HAND, int(2.6 * S))
check("back in the muzzle: rope and hook hidden, the shot over", first.shot is None and not look_shots.busy()
      and not look_shots.holds(shot)
      and look_fixture.shown(pieces) == 0 and first.hook.made.called("SetVisibility")[-1] == (False, False))

# Let go 0.35 s into a 0.4 s flight, 17 m out: back 0.35 s later, at 3.7 s.
early = look_shots.start(character, HAND, ANCHOR, 3 * S, 0.4)
look_shots.let_go(early, int(3.35 * S))
later = look_shots.start(character, HAND, ANCHOR, int(3.4 * S), 0.4)
second = places[1]
look_shots.tick(character, HAND, int(3.45 * S))
check("a new shot while the last hook comes back takes the other place, both shown",
      first.shot is not None and second.shot is not None and look_fixture.shown(first.rope.strands[0][0]) > 0
      and look_fixture.shown(second.rope.strands[0][0]) > 0)
look_shots.let_go(later, int(3.5 * S))
check("each shot let go by itself: both still out, coming back",
      look_shots.holds(early) and look_shots.holds(later))
third = look_shots.start(character, HAND, ANCHOR, int(3.55 * S), 0.4)
check("a third takes the place of the one let go the longest ago",
      first.shot.fired_ns == int(3.55 * S) and second.shot.fired_ns == int(3.4 * S))
look_shots.drop(third)
check("a shot dropped with the arm: its rope and hook gone at once, the other still out",
      not look_shots.holds(third) and look_shots.holds(later) and look_fixture.shown(first.rope.strands[0][0]) == 0
      and first.hook.made.called("SetVisibility")[-1] == (False, False))

look_settings.rope_look.value = "C"
look_shots.prepare(character)
check("new settings wait while a hook is still coming back", look_shots._places[0].rope.look == "A")
look_shots.tick(character, HAND, 10 * S)
old = list(record["pieces"])
look_shots.prepare(character)
check("once all are back, the old pieces are removed and C is built, with its glow",
      all(made.called("K2_DestroyComponent") for made in old)
      and look_shots._places[0].rope.look == "C" and len(look_shots._places[0].rope.strands) == 2
      and len(record["pieces"]) == len(old) + 2 * (2 * 69 + 1))

# C's glow is painted in its image: a new colour builds it again; its face lights at its share at each shot.
built_c = len(record["pieces"])
look_settings.rope_colour.value = "PURPLE"
look_shots.prepare(character)
glow_material = [made for made in record["materials"] if made.parent.path == look_assets.ROPE["halo"]["material"]][-1]
check("C in a new colour is built again, its glow in that colour's image, and said",
      len(record["pieces"]) == built_c + 2 * (2 * 69 + 1)
      and glow_material.called("SetTextureParameterValueByInfo")[-1][1].path
      == look_assets.ROPE["halo"]["images"]["PURPLE"]
      and any("and its glow in PURPLE" in line for line in state["misc"]))
look_settings.glow_face.value = "F"
lit = look_shots.start(character, HAND, ANCHOR, int(10.2 * S), 0.4)
rope_c = look_shots._places[0].rope
purple = rope_c.material.called("SetVectorParameterValueByInfo")[0][1]
check("a shot lights C's face at its share of the strength, in the colour chosen",
      [args[1] for args in rope_c.material.called("SetScalarParameterValueByInfo")] == [12.0 * 0.6] * 3
      and near([part * look_assets.GLOW_PAINTED[0] for part in (purple.R, purple.G, purple.B)],
               look_assets.COLOURS["PURPLE"], 1e-9))
look_shots.drop(lit)
look_settings.glow_face.value = "D"
look_settings.rope_colour.value = "ORANGE"
# The pieces before the last build, as the checks below take them.
old = record["pieces"][:-2 * (2 * 69 + 1)]

old = list(record["pieces"][len(old):])
before = len(record["pieces"])
character.destroyed = True
newcomer = look_fixture.dress(sdk_stubs.FakeCharacter(), record)
look_shots.tick(newcomer, HAND, 11 * S)
look_shots.prepare(newcomer)
check("a new character: the old pieces are forgotten, never called, and the new one gets its own",
      not any(made.called("K2_DestroyComponent") for made in old) and look_shots._mine(newcomer)
      and len(record["pieces"]) == before + len(old))

look_shots.reset()
check("reset removes every piece of a living character", not look_shots.built()
      and all(made.called("K2_DestroyComponent") for made in record["pieces"][-len(old):]))
look_settings.rope_look.value = "A"
gone = look_fixture.dress(sdk_stubs.FakeCharacter(), record)
look_shots.prepare(gone)
built_a = len(record["pieces"])
look_settings.rope_colour.value = "RED"
look_shots.prepare(gone)
check("A takes its colour at each shot: a new colour builds nothing again", len(record["pieces"]) == built_a)
look_settings.rope_colour.value = "ORANGE"
its_pieces = list(record["pieces"][-140:])
gone.destroyed = True
look_shots.reset()
check("reset after the character is gone forgets its pieces without calling them",
      not look_shots.built() and not any(made.called("K2_DestroyComponent") for made in its_pieces))

for pair in look_fixture.every_asset():
    state["objects"].pop(pair, None)
look_fixture.install(state, missing=(look_assets.PIECES["hook"]["mesh"],))
try:
    look_shots.prepare(newcomer)
    missing = None
except look_load.Missing as error:
    missing = error
check("without our container, nothing is built and the missing hook is named",
      missing is not None and missing.paths == [look_assets.PIECES["hook"]["mesh"]] and not look_shots.built())

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
