"""Tests what each companion is given in Companions (tuning_given.py): the starting settings give decision 67's
starting values, the characters' package's own; each setting turned into its value (a multiple, a share, a wait or
never, a speed factor, a wait); the refill at NEVER, never; the outfit kept for that hunter, his own for an ally; the
settings read when given() is called, never after; a value that is no number, a bool included, read as the slider's
starting one; what chose them said as the settings."""

import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from companions import settings, tuning_given  # noqa: E402
from companions.characters.companions import tuning  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


starting = tuning_given.given()("Crankus")
check("the starting settings: decision 67's starting values, the package's own", starting[:6] == tuning.STARTING[:6]
      and starting.said == ("settings", "companions"))
settings.health.value, settings.shield.value, settings.refill.value = 12, 70, 25
settings.speed.value, settings.back.value = 50, 90
settings.outfits.value = {"Vex": "player"}
given = tuning_given.given()
check("each setting turned into its value", given("Crankus")[:5] == (12.0, 0.7, 25.0, 1.5, 90.0))
check("the outfit kept for that hunter; his own for another and an ally", given("Vex").outfit == "player"
      and given("Rafa").outfit == "own" and given("Crankus").outfit == "own")
settings.health.value, settings.outfits.value = 3, {}
check("read when given() is called, never after", given("Vex").times == 12.0 and given("Vex").outfit == "player")
settings.refill.value = settings.NEVER
check("the refill at NEVER: never", tuning_given.given()("Crankus").refill_after_s is None)
settings.health.value, settings.shield.value, settings.speed.value = True, "x", math.nan
settings.back.value, settings.refill.value = None, [5]
odd = tuning_given.given()("Crankus")
check("no number, a bool included: the slider's starting one", odd[:5] == (4.0, 0.3, None, 1.2, 45.0))
check("within the package's bounds once checked", tuning.checked(odd) == odd)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
