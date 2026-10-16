"""Tests the normal mode's aim (normal/aim.py): the level's factors on every fire behaviour of an enemy's weapons, Value
and BaseValue, the sway and the empty slot left, a struct read as a copy written back too, the writes announced; met
again, a behaviour still holding them left, one the game changed taken from what it holds, never multiplied twice; no
weapon; given back where the values written are still there, left where the game changed them or freed the
behaviour; the behaviours held bounded, the freed forgotten first; a read that fails said."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

import aim_fixture  # noqa: E402
from it_follows.normal import aim, levels  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def enemy(*held: list | None) -> types.SimpleNamespace:
    return types.SimpleNamespace(ActiveWeapons=aim_fixture.weapons(*held))


GAME = {"aiaccuracy": [7.5, 7.5], "aiminaccuracy": [0.25, 0.25], "aiprojectilespeed": [0.45, 0.45]}

try:
    said: list[tuple] = []
    predator = levels.LEVELS["Predator"]
    aiming = aim.Aim(lambda call, log=True, **f: said.append((call, log, f)), predator.spread, predator.bullet_speed)
    gun = aim_fixture.Behaviour("Bandit_1.Gun.UM0_PC")
    copied = aim_fixture.Behaviour("Bandit_1.Pistol.UM0_PC", accuracy=6.0, copying=True)
    bandit = enemy([gun], None, [copied])
    check("given on every fire behaviour", aiming.give("Bandit_1", bandit) == "given")
    check("Predator's: spread x0.8, bullets x1.12, Value and BaseValue",
          gun.values() == {"aiaccuracy": [6.0, 6.0], "aiminaccuracy": [0.2, 0.2], "aiprojectilespeed": [0.504, 0.504]})
    check("through a struct read as a copy too", copied.values()["aiaccuracy"] == [4.8, 4.8])
    check("each write announced before, by behaviour", [entry[2]["behaviour"] for entry in said]
          == ["Bandit_1.Gun.UM0_PC", "Bandit_1.Pistol.UM0_PC"] and all(entry[0] == "WeaponAim" for entry in said))
    check("met again: held, never multiplied twice", aiming.give("Bandit_1", bandit) == "held"
          and gun.values()["aiaccuracy"] == [6.0, 6.0])
    gun.stored["aiprojectilespeed"].Value = 0.6
    gun.stored["aiprojectilespeed"].BaseValue = 0.6
    check("one field the game changed: what it holds taken for the game's, the level's on it; the others kept, "
          "never multiplied twice", aiming.give("Bandit_1", bandit) == "given"
          and gun.values()["aiprojectilespeed"] == [0.672, 0.672] and gun.values()["aiaccuracy"] == [6.0, 6.0]
          and aiming.by_enemy["Bandit_1"] == ["Bandit_1.Gun.UM0_PC", "Bandit_1.Pistol.UM0_PC"])
    check("given back where the level's still is", aiming.take_off("Bandit_1") == "given_back"
          and gun.values() == {**GAME, "aiprojectilespeed": [0.6, 0.6]}
          and copied.values()["aiaccuracy"] == [6.0, 6.0] and said[-1][2] == {"on": "Bandit_1", "back": True})
    check("once: then never given", aiming.take_off("Bandit_1") == "not_given" and aiming.held == {})

    float32 = aim_fixture.Behaviour("Body_7.Gun.UM0_PC", accuracy=12.0)
    aiming.give("Body_7", enemy([float32]))
    float32.stored["aiaccuracy"].Value = 9.6000003815
    check("a value read back in 32 bits is the one written", aiming.give("Body_7", enemy([float32])) == "held")
    float32.stored["aiaccuracy"].Value = 9.6002
    check("one 2e-4 away is not", aiming.give("Body_7", enemy([float32])) == "given")
    aiming.take_off("Body_7")
    reborn = aim_fixture.Behaviour("Body_2.Gun.UM0_PC")
    aiming.give("Body_2", enemy([reborn]))
    reborn.stored["aiaccuracy"].Value = 9.0
    check("a value the game put since: left as it is", aiming.take_off("Body_2") == "left"
          and reborn.values()["aiaccuracy"] == [9.0, 6.0])
    freed = aim_fixture.Behaviour("Gone_3.Gun.UM0_PC")
    aiming.give("Gone_3", enemy([freed]))
    freed.freed = True
    check("a behaviour the game freed: left", aiming.take_off("Gone_3") == "left")

    check("no weapon, or only a sway: nothing held", aiming.give("Psycho_4", enemy(None)) == "no_weapon"
          and aiming.give("Psycho_5", enemy([])) == "no_weapon" and aiming.held == {})
    check("a read that fails said", aiming.give("Broken_6", types.SimpleNamespace()) == "failed:AttributeError")

    aim.HELD_MOST = 2
    first, second = aim_fixture.Behaviour("A.Gun"), aim_fixture.Behaviour("B.Gun")
    aiming.give("A", enemy([first]))
    aiming.give("B", enemy([second]))
    third = aim_fixture.Behaviour("C.Gun")
    check("the behaviours held bounded", aiming.give("C", enemy([third])) == "full"
          and third.values() == GAME)
    first.freed = True
    check("the freed forgotten first, then room", aiming.give("C", enemy([third])) == "given"
          and list(aiming.held) == ["B.Gun", "C.Gun"])
    aim.HELD_MOST = 2000
    quiet = aim.Aim(lambda call, log=True, **f: said.append((call, log, f)), 0.88, 1.06)
    said.clear()
    for number in range(aim.DETAILED + 2):
        quiet.give(f"E{number}", enemy([aim_fixture.Behaviour(f"E{number}.Gun")]))
    check("the first DETAILED writes said in the log, the rest only made",
          [entry[1] for entry in said] == [True] * aim.DETAILED + [False, False])
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
