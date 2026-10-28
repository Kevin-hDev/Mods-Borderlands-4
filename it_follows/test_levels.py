"""Tests the five levels (decision 70: the sixth, 120, gone): their targets in order, each band within 90 to 105 % of
its target and its target inside it, Kevin's catch-up distances, the far threshold 20 m past them, Kevin's spread of the
distances at every level, the default level, and a value that is no level; no level bounds the enemies beyond the wave's
radius (decision 65)."""

import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows import levels  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


try:
    check("five levels, 25 to 100", list(levels.LEVELS) == [25, 40, 60, 80, 100]
          and all(key == value.target for key, value in levels.LEVELS.items()))
    check("each band is 90 to 105 % of its target, rounded inwards",
          all(one.low == math.ceil(0.9 * one.target) and one.high == math.floor(1.05 * one.target)
              for one in levels.LEVELS.values()))
    check("the bands Kevin and the trials used", (levels.LEVELS[40].low, levels.LEVELS[40].high) == (36, 42)
          and (levels.LEVELS[100].low, levels.LEVELS[100].high) == (90, 105)
          and (levels.LEVELS[25].low, levels.LEVELS[25].high) == (23, 26))
    check("Kevin's catch-up distances", [levels.LEVELS[key].behind_m for key in levels.LEVELS]
          == [40.0, 35.0, 35.0, 30.0, 30.0])
    check("brought back 20 m past them", all(one.far_m == one.behind_m + 20.0 for one in levels.LEVELS.values()))
    check("decision 66: Kevin's spread at every level until each is tuned, its shares making 100 %",
          levels.SPREAD == ((60, 0.0), (20, 10.0), (10, 15.0), (10, -5.0))
          and all(one.spread == levels.SPREAD for one in levels.LEVELS.values())
          and sum(share for share, _ in levels.SPREAD) == 100)
    check("the default level is 40, the one verified in game", levels.DEFAULT == 40
          and levels.level(levels.DEFAULT) is levels.LEVELS[40])
    check("a value that is no level gives the default", levels.level(55) is levels.LEVELS[40]
          and levels.level(120) is levels.LEVELS[40])
    check("decision 65: a level bounds nothing beyond the wave's radius",
          not hasattr(levels, "HORDE_SHARE") and not hasattr(levels.LEVELS[40], "most"))
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
