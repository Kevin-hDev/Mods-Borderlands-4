"""Tests the beam's strength: a damage per second that grows with the level."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import strength  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(found: float, wanted: float) -> bool:
    return abs(found - wanted) < 1e-6


check("at level 1 the beam deals the setting itself", near(strength.per_second(75, 1), 75.0))
check("each level adds nine percent", near(strength.per_second(100, 2), 109.0) and near(strength.per_second(100, 3), 118.81))
check("a level under 1 counts as 1", near(strength.per_second(75, 0), 75.0) and near(strength.per_second(75, -4), 75.0))
check("a runaway level is bounded", strength.per_second(1, 10 ** 9) == strength.per_second(1, strength.MAX_LEVEL))
check("a negative setting deals nothing", strength.per_second(-5, 10) == 0.0)
check("a hit is its share of a second", near(strength.per_hit(100, 1, 5), 20.0))
check("hits slower than one a second deal a whole second each", near(strength.per_hit(100, 1, 0.1), 100.0))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
