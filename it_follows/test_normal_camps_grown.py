"""Tests the camps grown (normal/camps_grown.py) on a real block of memory (param_fixture.py): a bandits' camp not born
grown x1.5 then reset without removing anyone, its empty numbers kept empty; a camp born, a chest's, a boss's
reinforcements, a total without end, an empty one left to the game; two camps of one enemy at x1.5 give one, then two,
the first neither written nor reset; a range grown whole; a camp held not read again, one the game loaded again taken
again; a far camp not held; the stop gives the numbers back, resets a camp still not born and not one born since; a
camp gone owes nothing; without a place, nothing; the pass stops at its time."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import param_fixture as fx  # noqa: E402
from it_follows import gbx_param  # noqa: E402
from it_follows.normal import camps_grown  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def number(spawner: object, field: str) -> object:
    return gbx_param.read(spawner.SpawnerComponent.SpawnerStyleData.InlineDef, field)[1]


def resets(name: str) -> list:
    return [args for called, args in calls if called == f"{name}.reset"]


HERE_CM = (0.0, 0.0, 0.0)

try:
    memory = fx.Memory()
    calls: list = []
    lines: list[tuple[str, dict]] = []
    announced: list[tuple[str, dict]] = []
    bandits = fx.camp("OakSpawner_Bandits", 50.0, fx.camp_style(memory, 4), calls)
    born = fx.camp("OakSpawner_Born", 60.0, fx.camp_style(memory, 4), calls, born=2)
    chest = fx.camp("OakSpawner_Chest", 70.0, fx.camp_style(memory, 3, style="SpawnerStyleDef_Bunch"), calls,
                    enemy="Lootable_AmmoChest_Ripper")
    boss_adds = fx.camp("OakSpawner_Adds", 80.0, fx.camp_style(memory, 2), calls, enemy="Char_GunToterSMG_BossAdd")
    endless = fx.camp("OakSpawner_Endless", 90.0, fx.camp_style(memory, 2147483647), calls)
    empty = fx.camp("OakSpawner_Empty", 95.0, fx.camp_style(memory, 0), calls)
    lone = fx.camp("OakSpawner_Lone", 100.0, fx.camp_style(memory, 1), calls, enemy="Char_GunToterSMG", total=1)
    lone_too = fx.camp("OakSpawner_LoneToo", 110.0, fx.camp_style(memory, 1), calls, enemy="Char_GruntPistol",
                       total=1)
    ranged = fx.camp("OakSpawner_Ranged", 120.0, fx.camp_style(memory, (6.0, 2.0), style="SpawnerStyleDef_Bunch"),
                     calls)
    far = fx.camp("OakSpawner_Far", 1500.0, fx.camp_style(memory, 4), calls)
    state["all"]["Spawner"] = [bandits, born, chest, boss_adds, endless, empty, lone, lone_too, ranged, far]
    grown = camps_grown.CampsGrown(lambda event, **f: lines.append((event, f)),
                                   lambda call, log=True, **f: announced.append((call, f)), 1.5)
    check("due at once", grown.due(0.0))
    done = grown.grow(HERE_CM, 10.0)
    check("what the pass did", {key: done[key] for key in ("grown", "same", "born", "not_enemies", "too_many",
                                                           "empty", "far", "stopped")}
          == {"grown": 3, "same": 1, "born": 1, "not_enemies": 2, "too_many": 1, "empty": 1, "far": 1,
              "stopped": "complete"})
    check("the bandits' camp: 6 in all, waves of 6, its empty number kept empty",
          number(bandits, "NumTotalActors") == 6 and number(bandits, "NumWaveActors") == 6
          and number(bandits, "NumWaveActorsPassive") == 0)
    check("then reset without removing anyone, and said", resets("OakSpawner_Bandits") == [(False,)]
          and ("normal_camp_grown", {"camp": "OakSpawner_Bandits", "enemy": "Mix_GRA_Bandit_Coastal",
                                     "total": [4, 6], "written": 2}) in lines)
    check("each write and reset announced first", announced[:2] == [
        ("SpawnerStyle", {"camp": "OakSpawner_Bandits", "enemy": "Mix_GRA_Bandit_Coastal", "factor": 1.5}),
        ("ResetSpawner", {"camp": "OakSpawner_Bandits"})])
    check("the born, the chest, the reinforcements, the endless and the empty camps untouched",
          all(not resets(camp.Name) for camp in (born, chest, boss_adds, endless, empty))
          and number(born, "NumTotalActors") == 4 and number(chest, "NumActors") == 3
          and number(boss_adds, "NumTotalActors") == 2)
    check("two camps of one enemy at x1.5: one, then two; the first not reset",
          number(lone, "NumTotalActors") == 1 and not resets("OakSpawner_Lone")
          and number(lone_too, "NumTotalActors") == 2 and resets("OakSpawner_LoneToo") == [(False,)])
    check("a range grown whole", number(ranged, "NumActors") == [9.0, 3.0])
    check("a far camp not held", "OakSpawner_Far" not in grown.held)

    before = len(calls)
    again = grown.grow(HERE_CM, 20.0)
    check("a camp held is not read again", len(calls) == before and again["grown"] == 0 and again["far"] == 1)
    bandits.freed = True
    reloaded = fx.camp("OakSpawner_Bandits", 50.0, fx.camp_style(memory, 4), calls)
    state["all"]["Spawner"] = [reloaded, born, lone_too, ranged]
    check("a camp the game loaded again is taken again", grown.grow(HERE_CM, 30.0)["grown"] == 1
          and number(reloaded, "NumTotalActors") == 6)

    lone_too.SpawnerComponent.GetNumSpawnedActors.answer = 1
    ranged.freed = True
    given = grown.put_back()
    check("the stop: numbers given back to the camps still there",
          given == {"given": 2, "reset": 1, "gone": 1, "failed": 0}
          and number(reloaded, "NumTotalActors") == 4 and number(lone_too, "NumTotalActors") == 1)
    check("a camp still not born reset again (the first one, the one loaded again, its give back), one born since not",
          resets("OakSpawner_Bandits") == [(False,)] * 3 and len(resets("OakSpawner_LoneToo")) == 1
          and grown.held == {})

    check("without a place, nothing", grown.grow(None, 40.0)["stopped"] == "no_place")
    first, second = (fx.camp(f"OakSpawner_Cap{number}", 50.0, fx.camp_style(memory, 4), calls) for number in (1, 2))
    state["all"]["Spawner"] = [first, second]
    camps_grown.MAX_HELD = 1
    capped = grown.grow(HERE_CM, 41.0)
    check("no more than MAX_HELD camps held at once", capped["stopped"] == "held_limit"
          and list(grown.held) == ["OakSpawner_Cap1"])
    first.freed = True
    state["all"]["Spawner"] = [second]
    written, reset = number(first, "NumTotalActors"), len(resets("OakSpawner_Cap1"))
    freed = grown.grow(HERE_CM, 42.0)
    check("a camp the game freed, no longer listed, is forgotten, its room given to a new one, nothing written on it",
          freed["stopped"] == "complete" and list(grown.held) == ["OakSpawner_Cap2"]
          and number(first, "NumTotalActors") == written and len(resets("OakSpawner_Cap1")) == reset)
    camps_grown.MAX_HELD = 2000
    grown.held = {}
    camps_grown.READ_S = -1.0
    check("the pass stops at its time", grown.grow(HERE_CM, 50.0)["stopped"] == "time_limit")
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
