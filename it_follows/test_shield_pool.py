"""Tests an enemy's shield as It Follows gives it (shield_pool): a shield of the game's type found by a field read; one
added with the game's own call (the shield's type, the pool chosen by the game, nothing refilled, no segments), its
pool the one that read nothing before, sized at the share of the health it held, written again for the game's bonus,
full; when no single new pool is read, none given, nothing written nor taken off; refilled over the time asked every
tenth of a second; taken off its own pool; each handle of the type its parameter wants, looked up once; a call that
fails raises and drops them all."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import health_fixture as game  # noqa: E402
from it_follows import shield_pool  # noqa: E402

game.install(state)
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


try:
    bandit = game.Enemy("Char_GunToterPistol", game.Pool(1000.0, bonus=1.2))
    shielded = game.Enemy("Char_GruntSMG", game.Pool(1000.0), game.Pool(500.0),
                          kinds=("HealthType_AI_Flesh", "HealthType_AI_Energy"))
    check("a shield of the game's type found by its health types", shield_pool.shielded(shielded)
          and not shield_pool.shielded(bandit))
    pool = shield_pool.ShieldPool()
    added = pool.add(bandit, 0.4)
    check("added with the game's own call: the shield's type, the pool chosen by the game, nothing refilled, no "
          "segments", game.of("AddHealthPool") == [("AddHealthPool", "Char_GunToterPistol", "HealthType_AI_Energy",
                                                    "ResourcePool_AI_Health_02", True, False, 1.0, [])])
    check("its pool the one that read nothing before, sized at 40 % of the health (1 200), written again for the "
          "game's bonus", added == (1, 480.0) and bandit.pools[1].most == 480.0
          and [call[3] for call in game.of("SetAttributeToFloat")] == [480.0, 384.0])
    check("full", bandit.pools[1].left == 480.0 and pool.fill(bandit, 1) == 1.0)
    check("the shield's type among the enemy's", game.types_of(bandit) == ["HealthType_AI_Flesh",
                                                                           "HealthType_AI_Energy"])
    armoured = game.Enemy("Char_Turret", game.Pool(300.0), game.Pool(700.0), kinds=("HealthType_AI_Armor",))
    check("the share taken of all the health it held, in the pool chosen", pool.add(armoured, 0.4) == (2, 400.0))
    game.calls.clear()
    check("taken off the pool it is in", pool.remove(armoured, 2) is True
          and [call[3] for call in game.of("RemoveHealthPool")] == ["ResourcePool_AI_Health_03"])

    class HalfFull(game.Damage):
        def AddHealthPool(self, **kwargs: object) -> int:
            super().AddHealthPool(**kwargs)
            kwargs["Context"].pools[1].left *= 0.25
            return 1

    state["classes"]["DamageStatics"] = game.Library("DamageStatics", HalfFull())
    partial = game.Enemy("Char_Partial", game.Pool(1000.0))
    check("one the game adds not full: filled", shield_pool.ShieldPool().add(partial, 0.4) == (1, 400.0)
          and partial.pools[1].left == 400.0)
    game.install(state)

    full = game.Enemy("Char_Full", game.Pool(100.0), game.Pool(100.0), game.Pool(100.0))
    game.calls.clear()
    check("no single new pool: none given, nothing written", pool.add(full, 0.4) is None
          and game.of("SetAttributeToFloat") == [] and game.of("RemoveHealthPool") == [])

    class TwoPools(game.Damage):
        def AddHealthPool(self, **kwargs: object) -> int:
            actor = kwargs["Context"]
            actor.pools[1], actor.pools[2] = game.Pool(10.0), game.Pool(10.0)
            game.give_type(actor, game.SHIELD)
            return 1

    state["classes"]["DamageStatics"] = game.Library("DamageStatics", TwoPools())
    odd = game.Enemy("Char_Odd", game.Pool(100.0))
    fresh = shield_pool.ShieldPool()
    game.calls.clear()
    check("two new pools: none given, nothing written nor taken off: a pool guessed could be the enemy's own",
          fresh.add(odd, 0.4) is None and game.of("SetAttributeToFloat") == [] and game.of("RemoveHealthPool") == [])
    game.install(state)

    game.calls.clear()
    pool.refill(bandit, 1.0 / 0.13)
    check("refilled over the time asked, the whole shield, every tenth of a second",
          game.of("RefillHealthPercentOvertime") == [("RefillHealthPercentOvertime", "Char_GunToterPistol",
                                                       "HealthType_AI_Energy", 1.0, 1.0, 7.692, 0.1)])
    check("taken off its own pool", pool.remove(bandit, 1) is True
          and game.of("RemoveHealthPool") == [("RemoveHealthPool", "Char_GunToterPistol", "HealthType_AI_Energy",
                                               "ResourcePool_AI_Health_02")]
          and bandit.pools[1] is None and game.types_of(bandit) == ["HealthType_AI_Flesh"])

    fresh = shield_pool.ShieldPool()
    game.calls.clear()
    for _ in range(2):
        fresh.add(game.Enemy("Char_Again", game.Pool(100.0)), 0.4)
        fresh.remove(bandit, 1)
    finds = [call[1:] for call in game.of("_find") if call[1] == "DamageStatics"]
    check("each handle looked up once, by the function and parameter it is for",
          finds == [("DamageStatics", "AddHealthPool"), ("DamageStatics", "AddHealthPool"),
                    ("DamageStatics", "RemoveHealthPool"), ("DamageStatics", "RemoveHealthPool")]
          and len([call for call in game.of("ClassDefaultObject") if call[1] == "DamageStatics"]) == 1)
    game.refused.add("RemoveHealthPool")
    try:
        fresh.remove(bandit, 1)
        raised = False
    except RuntimeError:
        raised = True
    game.refused.clear()
    game.calls.clear()
    fresh.remove(bandit, 1)
    check("a call that fails raises, and everything is built again at the next", raised
          and len([call for call in game.of("ClassDefaultObject") if call[1] == "DamageStatics"]) == 1
          and len([call for call in game.of("_find") if call[1] == "DamageStatics"]) == 2)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")
    import traceback
    traceback.print_exc()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
