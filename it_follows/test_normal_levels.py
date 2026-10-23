"""Tests the normal mode's four levels (normal/levels.py) against decisions 80 and 85: the camps grown, the chase, the
speed, the dodges' speed, chance and IsMovingSpeed, their rest divided by 20 at every level, the normal mode's own
Buffs; the shields of decision 112; the aim of decision 115; God, Predator with Senior's speeds, more health, damage
and rewards (decisions 153 and 155); Bandit at first; a name that is no level read as Bandit."""

import dataclasses
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
    return [getattr(levels.LEVELS[name], field) for name in ("Bandit", "Senior", "Predator", "God")]


try:
    check("four levels, in their order", list(levels.LEVELS) == ["Bandit", "Senior", "Predator", "God"]
          and all(level.name == name for name, level in levels.LEVELS.items()))
    check("camps x1.5, x2, x2, x2", column("camps") == [1.5, 2.0, 2.0, 2.0])
    check("the chase: 350 m for Bandit and Senior, 600 m for Predator and God, never the Horde's hunt",
          column("chase_m") == [350.0, 350.0, 600.0, 600.0])
    check("speed +20, +40, +50 %, God Senior's +40 % (decisions 100, 121 and 153)",
          column("speed") == [1.2, 1.4, 1.5, 1.4])
    check("the enemies' speed reducible at Senior, Predator and God (decisions 121 and 153)",
          column("reducible") == [False, True, True, True] and levels.REDUCED == 0.85)
    god, predator, senior_level = levels.LEVELS["God"], levels.LEVELS["Predator"], levels.LEVELS["Senior"]
    check("God is Predator but for Senior's run, dodges' speed and gestures, its health, damage and rewards",
          god == dataclasses.replace(predator, name="God", speed=senior_level.speed,
                                     dodge_speed=senior_level.dodge_speed, gestures=senior_level.gestures,
                                     health=3.5, taken=1.35, xp=0.25, ammo=0.50, cash=0.40))
    check("God reduced: as low as Senior reduced, never below Bandit",
          dataclasses.replace(levels.reduced(god), name="Senior")
          == dataclasses.replace(levels.reduced(senior_level), **{field: getattr(god, field) for field in (
              "camps", "chase_m", "dodge_chance", "dodge_moving", "health", "taken", "shield_refill", "spread",
              "bullet_speed", "xp", "ammo", "cash", "melee_rest", "staggers", "staggers_off")}))
    slower = levels.reduced(levels.LEVELS["Predator"])
    check("reduced: the run, the faster dodges and the gestures x0.85, nothing else",
          abs(slower.speed - 1.275) < 1e-9 and abs(slower.dodge_speed - 2.38) < 1e-9
          and abs(slower.gestures - 1.105) < 1e-9
          and slower == dataclasses.replace(levels.LEVELS["Predator"], speed=slower.speed,
                                            dodge_speed=slower.dodge_speed, gestures=slower.gestures))
    senior = levels.reduced(levels.LEVELS["Senior"])
    check("reduced at Senior: never below Bandit, run x1.2 and gestures x1.1, dodges x1.955 (decision 125)",
          senior.speed == 1.2 and senior.gestures == 1.1 and abs(senior.dodge_speed - 1.955) < 1e-9)
    check("each reduced level at or above Bandit in run, dodges and gestures",
          all(getattr(levels.reduced(levels.LEVELS[name]), field) >= getattr(levels.LEVELS["Bandit"], field)
              for name in ("Senior", "Predator", "God") for field in ("speed", "dodge_speed", "gestures")))
    check("Bandit, without the row, as it is", levels.reduced(levels.LEVELS["Bandit"]) is levels.LEVELS["Bandit"])
    check("dodges x1.7, x2.3, x2.8, God x2.3 faster (rebalance)", column("dodge_speed") == [1.7, 2.3, 2.8, 2.3])
    check("gestures x1.1, x1.2, x1.3, God x1.2 (decision 121)", column("gestures") == [1.1, 1.2, 1.3, 1.2])
    check("dodge chance 0.35, 0.45, 0.55, Predator the highest (rebalance)",
          column("dodge_chance") == [0.35, 0.45, 0.55, 0.55])
    check("IsMovingSpeed x100 for Predator and God", column("dodge_moving") == [1.0, 1.0, 100.0, 100.0])
    check("the armed bandits' rest (decision 126): the game's at Bandit, 3 to 5 s at Senior, 2 to 3 s at Predator; "
          "REDUCED leaves it", column("melee_rest") == [None, (4.0, 1.0), (2.5, 0.5), (2.5, 0.5)]
          and all(levels.reduced(levels.LEVELS[name]).melee_rest == levels.LEVELS[name].melee_rest
                  for name in levels.LEVELS))
    check("the rests divided by 20 at every level", levels.DODGE_REST_DIVIDE == 20.0)
    check("BUFF, BUFF+, BUFF++: health +45, +75, +130 %; damage taken +10, +20, +30 % (rebalance)",
          column("health") == [1.45, 1.75, 2.3, 3.5] and column("taken") == [1.1, 1.2, 1.3, 1.35])
    check("shields (decision 112): Bandit's an option, Senior's, Predator's and God's always; only Predator's and "
          "God's come back",
          column("shields") == [levels.OPTION, levels.ALWAYS, levels.ALWAYS, levels.ALWAYS]
          and column("shield_refill") == [False, False, True, True])
    check("40 % of the health; Predator's back 10 s after it breaks, 13 % a second",
          levels.SHIELD_SHARE == 0.4 and levels.SHIELD_REFILL_AFTER_S == 10.0 and levels.SHIELD_REFILL_RATE == 0.13)
    check("aim (decision 115): spread 12, 12 and 20 % tighter; bullets x1.06, x1.08, x1.12",
          column("spread") == [0.88, 0.88, 0.8, 0.8] and column("bullet_speed") == [1.06, 1.08, 1.12, 1.12])
    check("Bandit at first", levels.DEFAULT == "Bandit" and levels.level("Bandit") is levels.LEVELS["Bandit"])
    check("a name that is no level reads as Bandit", levels.level("Legend") is levels.LEVELS["Bandit"]
          and levels.level(None) is levels.LEVELS["Bandit"] and levels.level("Predator").name == "Predator")
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
