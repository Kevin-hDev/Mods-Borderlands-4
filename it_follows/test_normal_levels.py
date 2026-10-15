"""Tests the normal mode's three levels (normal/levels.py) against decisions 80 and 85: the camps grown, the chase, the
speed, the dodges' speed, chance and IsMovingSpeed, their rest divided by 20 at every level, the normal mode's own
Buffs; Bandit at first; a name that is no level read as Bandit."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows.normal import levels  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def column(field: str) -> list:
    return [getattr(levels.LEVELS[name], field) for name in ("Bandit", "Senior", "Predator")]


try:
    check("three levels, in their order", list(levels.LEVELS) == ["Bandit", "Senior", "Predator"]
          and all(level.name == name for name, level in levels.LEVELS.items()))
    check("camps x1.5, x2, x2", column("camps") == [1.5, 2.0, 2.0])
    check("the chase: 350 m for Bandit and Senior, 600 m for Predator, never the Horde's hunt",
          column("chase_m") == [350.0, 350.0, 600.0])
    check("speed +20, +50, +70 % (decision 100)", column("speed") == [1.2, 1.5, 1.7])
    check("dodges x1.7, x2.3, x2.8 faster (rebalance)", column("dodge_speed") == [1.7, 2.3, 2.8])
    check("dodge chance 0.35, 0.45, 0.55, Predator the highest (rebalance)",
          column("dodge_chance") == [0.35, 0.45, 0.55])
    check("IsMovingSpeed x100 for Predator only", column("dodge_moving") == [1.0, 1.0, 100.0])
    check("the rests divided by 20 at every level", levels.DODGE_REST_DIVIDE == 20.0)
    check("BUFF, BUFF+, BUFF++: health +45, +75, +130 %; damage taken +10, +20, +30 % (rebalance)",
          column("health") == [1.45, 1.75, 2.3] and column("taken") == [1.1, 1.2, 1.3])
    check("Bandit at first", levels.DEFAULT == "Bandit" and levels.level("Bandit") is levels.LEVELS["Bandit"])
    check("a name that is no level reads as Bandit", levels.level("Legend") is levels.LEVELS["Bandit"]
          and levels.level(None) is levels.LEVELS["Bandit"] and levels.level("Predator").name == "Predator")
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
