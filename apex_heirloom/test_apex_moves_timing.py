"""Tests the timing of the heirloom's draw and put-away: the draw's defaults are the ones Kevin set in game, and each
lies within its bounds."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import heirloom_stubs  # noqa: E402

heirloom_stubs.install()
from apex_heirloom import apex_moves_timing as moves_timing  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


timing = moves_timing.Timing()
check("the draw rises from 0.4 s at 0.8 times its speed, as Kevin set it in game on 2026-09-25",
      (timing.start, timing.speed) == (0.4, 0.8))
check("each default lies within its bounds, which the menu's sliders take",
      all(low <= getattr(timing, name) <= high for name, (low, high) in moves_timing.LIMITS.items()))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
