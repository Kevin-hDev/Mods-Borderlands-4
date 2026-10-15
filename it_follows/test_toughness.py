"""Tests BUFF and BUFF+ on the enemies (toughness), through the real health_pools over the fake game: Normal calls
nothing; each pool an enemy has raised to the game's own maximum times the factor, two writes when the game's bonus
shows, its share kept, a pool it lacks never written, the raise announced once before; an enemy raised once only;
one let go alive has the game's own maximum back with its share; one killed is never called on, only remembered, and
should a later run find its raised maximum still on that body, said and taken back as raised, the factor written from
the game's base, never laid twice, never so for a maximum near it by nature; a pool that
fails is said, those raised before it given back; the enemies tended, the ones detailed and the bodies remembered all
bounded. The Hardcore's factor changed during a game: reached on an enemy raised, one write a pool from the game's
base, its share kept, without a line; back to the level's; the enemies met next raised by the new factor; one never
raised said so; a pool that fails said."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import health_fixture as game  # noqa: E402
from it_follows import toughness as toughness_module  # noqa: E402

game.install(state)
fails: list[str] = []
notes: list[tuple] = []
announced: list[tuple] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def chaser(enemy: object) -> types.SimpleNamespace:
    """A chaser as It Follows holds it: its name, and its enemy through a weak pointer."""
    return types.SimpleNamespace(name=enemy.Name, actor=sdk_stubs.FakeWeak(enemy))


def toughness(factor: float) -> toughness_module.Toughness:
    return toughness_module.Toughness(lambda call, log=True, **fields: announced.append((call, log, fields)),
                                      lambda event, **fields: notes.append((event, fields)), factor)


def near(a: float, b: float) -> bool:
    return abs(a - b) <= 0.01 * b


try:
    normal = toughness(1.0)
    psycho = game.Enemy("Char_Psycho", game.Pool(1000.0))
    check("Normal raises nothing and calls nothing", normal.start([chaser(psycho)]) == 0 and game.calls == []
          and normal.tended == {} and notes == [] and announced == [])

    buff = toughness(1.2)
    # Health under a bonus of 1.3, full; a shield without bonus, half spent; no armor.
    psycho = game.Enemy("Char_Psycho", game.Pool(1000.0, bonus=1.3), game.Pool(500.0, share=0.5))
    check("Buff raises the enemy drawn", buff.start([chaser(psycho)]) == 1)
    check("its health to 1.2 times the game's maximum, still full",
          near(psycho.pools[0].most, 1560.0) and near(psycho.pools[0].left, 1560.0))
    check("its shield too, still half spent", near(psycho.pools[1].most, 600.0) and near(psycho.pools[1].left, 300.0))
    check("two writes where the game's bonus shows, one where none does, none for the pool it lacks",
          [call[1] for call in game.of("SetAttributeToFloat")]
          == ["ai_health_resource_01_max_value", "ai_health_resource_01_max_value", "ai_health_resource_02_max_value"])
    check("the raise announced once, before the first call, and written down",
          announced == [("SetAttributeToFloat", True, {"on": "Char_Psycho", "health": 1.2})]
          and notes == [("health_raised", {"on": "Char_Psycho", "pool_1": [1300, 1560], "pool_2": [500, 600]})])
    check("each pool kept with the game's own base and the maximum reached",
          [(pool, round(base), round(most)) for pool, base, most in buff.tended["Char_Psycho"]]
          == [(0, 1000, 1560), (1, 500, 600)])
    game.calls.clear()
    check("an enemy raised already is not raised again", buff.start([chaser(psycho)]) == 0
          and game.of("SetAttributeToFloat") == [])

    buff.harden(1.32)
    announced.clear()
    notes.clear()
    check("a new factor reached on an enemy raised: the game's maximum times it, its shares kept",
          buff.reach("Char_Psycho", psycho) == "reached" and near(psycho.pools[0].most, 1716.0)
          and near(psycho.pools[0].left, 1716.0) and near(psycho.pools[1].most, 660.0)
          and near(psycho.pools[1].left, 330.0))
    check("one write a pool, from the game's base, announced without a line",
          [(call[1], call[3]) for call in game.of("SetAttributeToFloat")]
          == [("ai_health_resource_01_max_value", 1320.0), ("ai_health_resource_02_max_value", 660.0)]
          and announced == [("SetAttributeToFloat", False, {"on": "Char_Psycho", "health": 1.32})] and notes == [])
    check("the maxima reached kept", [round(most) for _, _, most in buff.tended["Char_Psycho"]] == [1716, 660])
    check("one never raised is said so", buff.reach("Char_Nobody", psycho) == "not_raised")
    fresh = game.Enemy("Char_Fresh", game.Pool(100.0))
    check("an enemy met next raised by the new factor", buff.start([chaser(fresh)]) == 1
          and near(fresh.pools[0].most, 132.0) and buff.put_back("Char_Fresh", fresh, False) == "restored")
    buff.harden(1.2)
    game.calls.clear()
    check("back to the level's", buff.reach("Char_Psycho", psycho) == "reached"
          and near(psycho.pools[0].most, 1560.0) and near(psycho.pools[0].left, 1560.0)
          and near(psycho.pools[1].most, 600.0) and near(psycho.pools[1].left, 300.0))
    game.refused.add("SetAttributeToFloat")
    check("a pool that fails is said", buff.reach("Char_Psycho", psycho) == "failed:RuntimeError")
    game.refused.discard("SetAttributeToFloat")

    psycho.pools[0].left = 780.0
    check("let go alive, it is given back", buff.put_back("Char_Psycho", psycho, False) == "restored"
          and "Char_Psycho" not in buff.tended)
    check("its maxima the game's own again, its shares kept",
          near(psycho.pools[0].most, 1300.0) and near(psycho.pools[0].left, 650.0)
          and near(psycho.pools[1].most, 500.0) and near(psycho.pools[1].left, 250.0))
    check("one never raised is said so, one whose enemy is gone too",
          buff.put_back("Char_Psycho", psycho, False) == "not_raised"
          and buff.start([chaser(game.Enemy("Char_Gone", game.Pool(10.0)))]) == 1
          and buff.put_back("Char_Gone", None, False) == "unavailable")

    rat = game.Enemy("Char_Rat", game.Pool(100.0))
    buff.start([chaser(rat)])
    game.calls.clear()
    check("killed, it is never called on, only remembered", buff.put_back("Char_Rat", rat, True) == "left"
          and game.calls == [] and "Char_Rat" not in buff.tended
          and toughness_module._left["Char_Rat"] == [(0, 100.0, 120.0)])
    later = toughness(1.4)
    notes.clear()
    check("a later run finding its raised maximum still on that body says so", later.start([chaser(rat)]) == 1
          and ("health_kept_on_body", {"on": "Char_Rat", "most": 120}) in notes
          and "Char_Rat" not in toughness_module._left)
    check("and takes it back as raised: the new factor from the game's base, 140 and never 168",
          near(rat.pools[0].most, 140.0) and later.tended["Char_Rat"][0][1] == 100.0)
    check("let go alive then, it has the game's own maximum back", later.put_back("Char_Rat", rat, False)
          == "restored" and near(rat.pools[0].most, 100.0))
    rat_again = game.Enemy("Char_Rat2", game.Pool(100.0))
    later.start([chaser(rat_again)])
    later.put_back("Char_Rat2", rat_again, True)
    rat_again.pools[0].base = 100.0
    notes.clear()
    later.start([chaser(rat_again)])
    check("one the game set again says nothing", [event for event, _ in notes] == ["health_raised"])
    rat_up = game.Enemy("Char_Rat3", game.Pool(100.0))
    later.start([chaser(rat_up)])
    later.put_back("Char_Rat3", rat_up, True)
    # Trial 19: the game's own maximum two levels up, 0.3 % from the one raised.
    rat_up.pools[0].base = 140.0 * 1.003
    notes.clear()
    later.start([chaser(rat_up)])
    check("one holding by nature a maximum 0.3 % from the one raised says nothing",
          [event for event, _ in notes] == ["health_raised"])

    empty = game.Enemy("Char_Ghost")
    notes.clear()
    check("an enemy with no pool is neither raised nor kept, and said so", buff.start([chaser(empty)]) == 0
          and "Char_Ghost" not in buff.tended and notes == [("health_raised", {"on": "Char_Ghost", "pools": 0})])

    game.refused.add("GetResourcePoolPercent")
    notes.clear()
    broken = game.Enemy("Char_Broken", game.Pool(100.0))
    check("a pool that fails is said, the enemy not counted", buff.start([chaser(broken)]) == 0
          and notes == [("health_raised", {"on": "Char_Broken", "failed": "RuntimeError"})]
          and "Char_Broken" not in buff.tended)
    game.refused.clear()
    half = game.Enemy("Char_Half", game.Pool(100.0), game.Pool(50.0))
    game.refused.add("AdjustResourcePoolValue")
    half.pools[1].left = 25.0
    buff.start([chaser(half)])
    game.refused.clear()
    check("the pools raised before a failure are kept, to be given back",
          [pool for pool, _base, _most in buff.tended["Char_Half"]] == [0]
          and buff.put_back("Char_Half", half, False) == "restored" and near(half.pools[0].most, 100.0))

    crowd = toughness(1.2)
    crowd.tended = {f"Char_{n}": [] for n in range(toughness_module.TENDED_MOST)}
    notes.clear()
    check("past TENDED_MOST enemies, a new one is refused and said",
          crowd.start([chaser(game.Enemy("Char_More", game.Pool(10.0)))]) == 0
          and notes == [("health_refused", {"on": "Char_More", "tended": toughness_module.TENDED_MOST})])

    quiet = toughness(1.2)
    notes.clear()
    many = [game.Enemy(f"Char_Q{n}", game.Pool(10.0)) for n in range(toughness_module.DETAILED + 5)]
    raised = quiet.start([chaser(enemy) for enemy in many])
    check("DETAILED enemies written down one by one, the rest only counted",
          raised == len(many) and len(notes) == toughness_module.DETAILED)

    toughness_module._left.clear()
    long_run = toughness(1.2)
    for number in range(toughness_module.LEFT_MOST + 5):
        enemy = game.Enemy(f"Char_K{number}", game.Pool(10.0))
        long_run.start([chaser(enemy)])
        long_run.put_back(enemy.Name, enemy, True)
    check("the bodies remembered bounded, the oldest forgotten first, no enemy kept once let go",
          len(toughness_module._left) == toughness_module.LEFT_MOST and "Char_K0" not in toughness_module._left
          and f"Char_K{toughness_module.LEFT_MOST + 4}" in toughness_module._left and long_run.tended == {})
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
