"""Tests an enemy's health pools where the game keeps them (health_pools): the maximum read with the game's bonus, the
default asked for a pool the enemy lacks; a base written and the maximum read after it; the share left, given back up
or down, nothing called when already there or for an empty pool; each library and each handle looked up once; a call
that fails raises and drops them all, built again at the next."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import health_fixture as game  # noqa: E402
from characters import health_pools  # noqa: E402

game.install(state)
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


try:
    check("three pools, from Resource_AI_Health_01 to 03, each with its maximum's attribute",
          health_pools.POOLS == (("ai_health_resource_01_max_value", "Resource_AI_Health_01"),
                                 ("ai_health_resource_02_max_value", "Resource_AI_Health_02"),
                                 ("ai_health_resource_03_max_value", "Resource_AI_Health_03")))
    pools = health_pools.HealthPools()
    enemy = game.Enemy("Char_Psycho", game.Pool(1000.0, bonus=1.3), game.Pool(500.0, share=0.5))
    check("the maximum read with the game's bonus", pools.most(enemy, 0) == 1300.0 and pools.most(enemy, 1) == 500.0)
    check("a pool the enemy lacks reads the default asked, below zero", pools.most(enemy, 2) == health_pools.UNREAD < 0)
    check("a base written, the maximum read after it with the bonus", pools.set_base(enemy, 0, 2000.0) == 2600.0
          and game.of("SetAttributeToFloat")[-1] == ("SetAttributeToFloat", "ai_health_resource_01_max_value",
                                                     "Char_Psycho", 2000.0))
    check("the pool keeps what it held when its maximum grows (MV1)", enemy.pools[0].left == 1300.0
          and pools.share(enemy, 0) == 0.5)
    pools.set_share(enemy, 0, 1.0)
    check("its share given back up", enemy.pools[0].left == 2600.0 and pools.share(enemy, 0) == 1.0)
    pools.set_share(enemy, 1, 0.2)
    check("or down", abs(enemy.pools[1].left - 100.0) < 1e-6)
    game.calls.clear()
    pools.set_share(enemy, 1, 0.2)
    pools.set_share(enemy, 2, 1.0)
    check("nothing adjusted when the share is already there, nor for a pool it lacks",
          game.of("AdjustResourcePoolValue") == [])
    check("each library's default object and each handle looked up once: only the third pool's handle, never used",
          [call[1:] for call in game.of("_find")] == [("GameResourcePoolFunctionLibrary", "GetResourcePoolValue")]
          and game.of("ClassDefaultObject") == [])

    fresh = health_pools.HealthPools()
    game.calls.clear()
    for _ in range(3):
        fresh.most(enemy, 0)
        fresh.set_base(enemy, 0, 1000.0)
        fresh.share(enemy, 1)
    check("built at the first use only: two libraries, one handle for the attribute written and one for the pool",
          len(game.of("ClassDefaultObject")) == 2
          and [call[1:] for call in game.of("_find")] == [("GbxAttributeBlueprintLibrary", "SetAttributeToFloat"),
                                                          ("GameResourcePoolFunctionLibrary", "GetResourcePoolValue")])
    game.refused.add("GetResourcePoolPercent")
    try:
        fresh.share(enemy, 0)
        raised = False
    except RuntimeError:
        raised = True
    game.refused.clear()
    game.calls.clear()
    fresh.share(enemy, 0)
    check("a call that fails raises, and everything is built again at the next",
          raised and len(game.of("ClassDefaultObject")) == 1 and len(game.of("_find")) == 1)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
