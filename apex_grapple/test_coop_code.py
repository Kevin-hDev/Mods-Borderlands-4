"""Tests coop_code.py and look_code.py: a direction comes back from its number within two hundredths of a degree,
whatever its length, every way round; a rope, a look and the release never take each other's numbers nor the game's
0; only a number sent with no target is ours; every look comes back from its number, and a number of another build
gives a rope shown."""

import itertools
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from apex_grapple import coop_code, look_code, look_settings, settings  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def angle(a: tuple, b: tuple) -> float:
    dot = sum(x * y for x, y in zip(a, b)) / (math.dist(a, (0, 0, 0)) * math.dist(b, (0, 0, 0)))
    return math.degrees(math.acos(max(-1.0, min(1.0, dot))))


# Ropes.
worst = 0.0
kinds = set()
for yaw in range(-180, 181, 7):
    for pitch in range(-89, 90, 6):
        r_yaw, r_pitch = math.radians(yaw + 0.37), math.radians(pitch + 0.21)
        way = (math.cos(r_pitch) * math.cos(r_yaw) * 1800.0, math.cos(r_pitch) * math.sin(r_yaw) * 1800.0,
               math.sin(r_pitch) * 1800.0)
        code = coop_code.encode_rope(way)
        worst = max(worst, angle(way, coop_code.decode_rope(code)))
        kinds.add(coop_code.kind(code))
        if not 0 <= code < 2 ** 32:
            fails.append(f"out of 32 bits: {code}")
check(f"every way round, the direction comes back within two hundredths of a degree (worst {worst:.4f})", worst < 0.02)
check("about 1 cm at 60 m", math.radians(360 / coop_code.TURN) * 6000 < 1.2)
check("every rope is of the rope kind", kinds == {coop_code.ROPE})
check("the length does not matter", coop_code.encode_rope((3.0, 4.0, 0.0)) == coop_code.encode_rope((300.0, 400.0, 0.0)))
check("straight up and straight down both come back",
      angle((0, 0, 1), coop_code.decode_rope(coop_code.encode_rope((0, 0, 1)))) < 0.02
      and angle((0, 0, -1), coop_code.decode_rope(coop_code.encode_rope((0, 0, -1)))) < 0.02)
check("a rope never takes the game's 0 nor the release's number",
      coop_code.encode_rope((-1e-9, 0.0, -1.0)) not in (0, coop_code.RELEASE))
try:
    coop_code.encode_rope((0.0, 0.0, 0.0))
    check("a direction with no length is refused", False)
except ValueError:
    check("a direction with no length is refused", True)

# Looks.
check("every look fits in what a message carries", look_code.COUNT - 1 <= coop_code.PAYLOAD)
check("a look comes back from its message", all(coop_code.decode_look(coop_code.encode_look(n)) == n
                                                for n in (0, 1, 12345, look_code.COUNT - 1)))
check("a look is of the look kind, never a rope", coop_code.kind(coop_code.encode_look(0)) == coop_code.LOOK
      and coop_code.encode_look(0) not in (0, coop_code.RELEASE))
check("the release is of neither kind", coop_code.kind(coop_code.RELEASE) not in (coop_code.ROPE, coop_code.LOOK))
try:
    coop_code.encode_look(coop_code.PAYLOAD + 1)
    check("a look out of range is refused", False)
except ValueError:
    check("a look out of range is refused", True)

check("no target and a number: ours", coop_code.is_ours(None, 1234))
check("no target and 0: the game's own 'no target'", not coop_code.is_ours(None, 0))
check("a target: the game's own", not coop_code.is_ours(object(), 3497936138))

samples = list(itertools.islice(itertools.product(*[option.choices for option in look_settings.ALL]), 0, None, 997))
check("every look comes back from its number", all(
    look_code.decode(look_code.encode(shown, values)) == look_code.Look(shown, tuple(values))
    for values in samples for shown in (True, False)))
chosen = look_code.decode(look_code.encode(True, tuple(option.choices[-1] for option in look_settings.ALL)))
check("a look reads by the settings' names", chosen.rope_colour == look_settings.rope_colour.choices[-1]
      and chosen.look == look_settings.CLASSIC and chosen.shown)
other = look_code.decode(look_code.COUNT + 5)
check("a number of another build gives a rope shown, in the first value of each setting",
      other.shown and other.values == tuple(option.choices[0] for option in look_settings.ALL))
look_settings.rope_colour.value = "GREEN"
settings.show_rope.value = False
mine = look_code.decode(look_code.mine())
check("the player's own look is read from the settings in use", mine.rope_colour == "GREEN" and not mine.shown)
settings.show_rope.value = True

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
