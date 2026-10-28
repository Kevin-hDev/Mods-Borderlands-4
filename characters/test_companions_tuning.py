"""Tests what a companion is given by its mod (companions/tuning.py): values within their bounds kept as given; each
one out of its bounds brought back to the nearest bound; anything that is no number, a bool included, read as the
starting value; no refill kept as none; an outfit unknown read as his own; what chose the values cut short, or empty
when it is no text; anything that is no Tuning read as the starting values, those of decision 67; the values as the
journal writes them."""

import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from characters.companions import tuning  # noqa: E402
from characters.companions.tuning import Tuning  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


GIVEN = Tuning(9.0, 0.3, 45.0, 1.3, 45.0, "player", ("Predator", "normal"))
check("within the bounds: kept as given", tuning.checked(GIVEN) == GIVEN)
check("the starting values of decision 67: 4 times, 30 %, never filled again, +20 %, 45 s, his own outfit",
      tuning.STARTING[:6] == (4.0, 0.3, None, 1.2, 45.0, "own"))
check("the bounds of decision 67's ranges", (tuning.TIMES, tuning.SHIELD, tuning.REFILL_AFTER_S, tuning.SPEED,
      tuning.BACK_AFTER_S) == ((1.0, 20.0), (0.0, 1.0), (5.0, 120.0), (1.0, 1.5), (10.0, 120.0)))
low = tuning.checked(Tuning(0.0, -1.0, 1.0, 0.5, 0.0, "own", ("a", "b")))
check("below the bounds: brought up to each low bound", low[:5] == (1.0, 0.0, 5.0, 1.0, 10.0))
high = tuning.checked(Tuning(50, 3, 900, 4, 1000, "own", ("a", "b")))
check("above the bounds: brought down to each high bound, an integer read as a number", high[:5] == (
      20.0, 1.0, 120.0, 1.5, 120.0) and all(type(value) is float for value in high[:5]))
odd = tuning.checked(Tuning(True, "x", "soon", None, math.nan, ["player"], ("a", "b")))
check("no number, a bool included, nor a NaN: the starting value; no refill when it is none",
      odd[:5] == (4.0, 0.3, None, 1.2, 45.0))
check("an outfit unknown: his own", odd.outfit == "own")
check("no refill given: kept as none", tuning.checked(GIVEN._replace(refill_after_s=None)).refill_after_s is None)
check("an infinite health: the starting one", tuning.checked(GIVEN._replace(times=math.inf)).times == 4.0)
check("what chose them cut short to MAX_TEXT", tuning.checked(GIVEN._replace(said=("x" * 99, "why"))).said == (
      "x" * tuning.MAX_TEXT, "why"))
check("what chose them, no text: empty; no pair: the starting one", tuning.checked(GIVEN._replace(
      said=(3, None))).said == ("", "") and tuning.checked(GIVEN._replace(said=["a", "b"])).said == ("starting",
                                                                                                    "unread"))
check("no Tuning at all: the starting values", tuning.checked(None) is tuning.STARTING
      and tuning.checked((9.0, 0.3, None, 1.2, 45.0, "own", ("a", "b"))) is tuning.STARTING)
check("as the journal writes them, what chose them last", tuning.written(GIVEN) == [
      9.0, 0.3, 45.0, 1.3, 45.0, "player", "Predator", "normal"])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
