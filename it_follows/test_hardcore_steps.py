"""Tests the Hardcore's rule (hardcore_steps.py, decisions 89 and 109): a whole step each 100 kills, nothing below
nothing, and the factor 1 % a step."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows import hardcore_steps as steps  # noqa: E402
from it_follows.normal import hardcore  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


try:
    check("Kevin's step, 100 kills, the normal mode's too", steps.KILLS_PER_STEP == 100 == hardcore.KILLS_PER_STEP)
    check("a whole step each 100 kills, cut", [steps.percent(kills) for kills in (0, 99, 100, 199, 816)]
          == [0, 0, 1, 1, 8])
    check("kills below nothing reach nothing", steps.percent(-5) == 0)
    check("1 % a step", steps.factor(0) == 1.0 and abs(steps.factor(8) - 1.08) <= 1e-12)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
