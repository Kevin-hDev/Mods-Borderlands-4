"""Tests the normal mode's shields (normal/shields.py) on the health fixture: one given to an enemy without, 40 % of its
health, announced before; none to one with the game's own, nor twice; past GIVEN_MOST refused; a failure said, the
enemy left without. Predator's broken shield refilled REFILL_AFTER_S after it broke, not before, over 1/REFILL_RATE s,
once at a time, again when broken after; a shield holding resets the wait; Bandit's and Senior's never refilled.
Taken off the living; one dead or away only remembered, never called on; an enemy met again under that name still
holding the shield given taken back as given, one whose shield differs left as the game's; the bodies remembered
bounded. An enemy whose three pools are all taken (a Vile Creep) gets none, nor one whose pools read nothing, the
game never asked; one asked with no single new pool read after is given none and never taken off. The first
NOTED_MOST without room or with no_pool written down with their health types and pools."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import health_fixture as game  # noqa: E402
from it_follows.normal import levels, shields  # noqa: E402

game.install(state)
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


announced: list[tuple] = []


def announce(call: str, log: bool = True, **fields: object) -> None:
    announced.append((call, fields.get("on")))
    game.calls.append(("announce", call, fields.get("on")))


def before(call: str) -> bool:
    """Whether the call was announced before the game's first call of that name."""
    made = [index for index, entry in enumerate(game.calls) if entry[0] == call]
    said = [index for index, entry in enumerate(game.calls) if entry[:2] == ("announce", call)]
    return bool(made) and bool(said) and said[0] < made[0]


def bandit(name: str) -> game.Enemy:
    return game.Enemy(name, game.Pool(1000.0))


try:
    calm = shields.Shields(announce, refill=False)
    one = bandit("Char_GunToterPistol_1")
    check("given to an enemy without one: 40 % of its health", calm.give(one.Name, one) == "given"
          and one.pools[1].most == 400.0 and calm.given[one.Name].pool == 1)
    check("announced before it is made", before("AddHealthPool"))
    check("never twice", calm.give(one.Name, one) == "held" and len(game.of("AddHealthPool")) == 1)
    grunt = game.Enemy("Char_GruntSMG_2", game.Pool(1000.0), game.Pool(300.0),
                       kinds=("HealthType_AI_Flesh", "HealthType_AI_Energy"))
    check("none to one with the game's own", calm.give(grunt.Name, grunt) == "had_one"
          and len(game.of("AddHealthPool")) == 1 and grunt.Name not in calm.given)
    one.pools[1].left = 0.0
    check("Bandit's and Senior's never refilled", calm.keep(one.Name, one, 0.0) is None
          and calm.keep(one.Name, one, 100.0) is None and game.of("RefillHealthPercentOvertime") == [])
    game.refused.add("AddHealthPool")
    broken = bandit("Char_Broken_3")
    check("a failure said, the enemy left without", calm.give(broken.Name, broken) == "failed:RuntimeError"
          and broken.Name not in calm.given)
    game.refused.clear()
    game.calls.clear()
    check("a shield given taken off the living, announced before", calm.take_off(one.Name, one, alive=True)
          == "removed" and before("RemoveHealthPool")
          and one.pools[1] is None and game.types_of(one) == ["HealthType_AI_Flesh"])
    check("one never given: nothing", calm.take_off(grunt.Name, grunt, alive=True) == "none"
          and len(game.of("RemoveHealthPool")) == 1)

    hunter = shields.Shields(announce, refill=True)
    prey = bandit("Char_Psycho_4")
    hunter.give(prey.Name, prey)
    check("a shield holding: nothing", hunter.keep(prey.Name, prey, 10.0) is None)
    prey.pools[1].left = 0.0
    check("broken: said, the wait begins", hunter.keep(prey.Name, prey, 20.0) == "broken")
    check("no refill before REFILL_AFTER_S", hunter.keep(prey.Name, prey, 29.9) is None
          and game.of("RefillHealthPercentOvertime") == [])
    game.calls.clear()
    check("refilled REFILL_AFTER_S after it broke, over 1/REFILL_RATE s, announced before",
          hunter.keep(prey.Name, prey, 30.0) == "refilled" and before("RefillHealthPercentOvertime")
          and game.of("RefillHealthPercentOvertime") == [("RefillHealthPercentOvertime", prey.Name,
                                                           "HealthType_AI_Energy", 1.0, 1.0, 7.692, 0.1)])
    check("once at a time: broken again during the refill, nothing until its end",
          hunter.keep(prey.Name, prey, 33.0) is None and hunter.keep(prey.Name, prey, 37.0) is None
          and len(game.of("RefillHealthPercentOvertime")) == 1)
    check("still broken after it: the wait again, then a second refill",
          hunter.keep(prey.Name, prey, 38.0) == "broken" and hunter.keep(prey.Name, prey, 47.9) is None
          and hunter.keep(prey.Name, prey, 48.0) == "refilled")
    check("the level's values", levels.SHIELD_REFILL_AFTER_S == 10.0 and levels.SHIELD_REFILL_RATE == 0.13)
    other = bandit("Char_Psycho_5")
    hunter.give(other.Name, other)
    other.pools[1].left = 0.0
    hunter.keep(other.Name, other, 0.0)
    other.pools[1].left = 1.0
    hunter.keep(other.Name, other, 5.0)
    other.pools[1].left = 0.0
    check("a shield holding again resets the wait", hunter.keep(other.Name, other, 6.0) == "broken"
          and hunter.keep(other.Name, other, 15.0) is None)

    game.calls.clear()
    check("one dead only remembered, never called on", hunter.take_off(other.Name, other, alive=False) == "left"
          and game.calls == [] and other.Name in shields._left)
    check("one away too", hunter.take_off(prey.Name, None, alive=True) == "left" and game.calls == [])
    again = shields.Shields(announce, refill=True)
    check("met again still holding the shield given: taken back as given, never given a second",
          again.give(other.Name, other) == "taken_back" and again.given[other.Name].pool == 1
          and game.of("AddHealthPool") == [] and other.Name not in shields._left)
    reused = bandit("Char_Psycho_4")
    reused.pools[1] = game.Pool(999.0)
    game.give_type(reused, game.SHIELD)
    check("a body met again whose shield differs: the game's, left alone", again.give(reused.Name, reused)
          == "had_one" and reused.Name not in again.given)

    shields._left.clear()
    many = shields.Shields(announce, refill=False)
    for index in range(shields.LEFT_MOST + 5):
        many.given[f"Char_{index}"] = shields.Given(1, 1.0)
    check("past GIVEN_MOST refused", many.give("Char_More", bandit("Char_More")) == "refused")
    for index in range(shields.LEFT_MOST + 5):
        many.take_off(f"Char_{index}", None, alive=False)
    check("the bodies remembered bounded, the oldest forgotten first", len(shields._left) == shields.LEFT_MOST
          and "Char_0" not in shields._left and f"Char_{shields.LEFT_MOST + 4}" in shields._left)

    noted: list[tuple] = []
    told = shields.Shields(announce, refill=True, note=lambda event, **fields: noted.append((event, fields)))
    vile = game.Enemy("Char_CreepCorrupt_6", game.Pool(222172.0), game.Pool(7935.0), game.Pool(7935.0),
                      kinds=("HealthType_AI_Flesh", "HealthType_Test_Other"))
    announced.clear()
    game.calls.clear()
    check("all three pools taken: none, the game never asked nor the call announced",
          told.give(vile.Name, vile) == "no_room" and game.of("AddHealthPool") == [] and announced == []
          and game.types_of(vile) == ["HealthType_AI_Flesh", "HealthType_Test_Other"] and vile.Name not in told.given)
    check("written down with its health types and pools", noted == [("normal_shield_no_room", {
        "on": vile.Name, "types": ["HealthType_AI_Flesh", "HealthType_Test_Other"], "pools": [222172, 7935, 7935]})])
    check("nothing to keep nor take off", told.keep(vile.Name, vile, 100.0) is None
          and told.take_off(vile.Name, vile, alive=True) == "none" and game.of("RemoveHealthPool") == [])
    for index in range(shields.NOTED_MOST + 3):
        crowd = game.Enemy(f"Char_Vile_{index}", game.Pool(10.0), game.Pool(1.0), game.Pool(1.0))
        told.give(crowd.Name, crowd)
    check("the first NOTED_MOST written down, a game", len(noted) == shields.NOTED_MOST
          and shields.NOTED_MOST == 20)
    untyped = shields.Shields(announce, refill=False, note=lambda event, **fields: noted.append((event, fields)))
    blind = game.Enemy("Char_Blind", game.Pool(10.0), game.Pool(1.0), game.Pool(1.0))
    real_types, real_shielded = shields.health_pools.types, shields.shield_pool.shielded

    def unreadable(actor: object) -> list[str]:
        raise AttributeError("HealthTypeStates")

    # The types read for the line only: the shield's own check is the field read tested above.
    shields.health_pools.types, shields.shield_pool.shielded = unreadable, lambda actor: False
    try:
        outcome = untyped.give(blind.Name, blind)
    finally:
        shields.health_pools.types, shields.shield_pool.shielded = real_types, real_shielded
    check("types that cannot be read for the line: said so, the enemy still left without", outcome == "no_room"
          and noted[-1][1]["types"] == "unread:AttributeError")

    noted.clear()
    watched = shields.Shields(announce, refill=True, note=lambda event, **fields: noted.append((event, fields)))
    bat = game.Enemy("Char_BatRanged_7")
    announced.clear()
    game.calls.clear()
    check("pools that read nothing: none, the game never asked nor the call announced, no line",
          watched.give(bat.Name, bat) == "unread" and game.of("AddHealthPool") == [] and announced == []
          and noted == [] and bat.Name not in watched.given and game.types_of(bat) == ["HealthType_AI_Flesh"])

    odd = game.Enemy("Char_Odd_8", None, game.Pool(50.0))
    game.calls.clear()
    check("asked, but no single new pool read after: none given, nothing written nor taken off",
          watched.give(odd.Name, odd) == "no_pool" and len(game.of("AddHealthPool")) == 1
          and odd.Name not in watched.given and game.of("SetAttributeToFloat") == [])
    check("written down with its types and pools before and after", noted == [("normal_shield_no_pool", {
        "on": odd.Name, "types": ["HealthType_AI_Flesh"], "pools": [-1, 50, -1],
        "types_after": ["HealthType_AI_Flesh", "HealthType_AI_Energy"], "pools_after": [-1, 50, -1]})])
    check("what the game laid is never taken off, and met again it reads as the game's",
          watched.take_off(odd.Name, odd, alive=True) == "none" and game.of("RemoveHealthPool") == []
          and shields.Shields(announce, refill=False).give(odd.Name, odd) == "had_one")
    watched.noted = shields.NOTED_MOST
    check("the lines without room and with no_pool share NOTED_MOST", watched.give(
        "Char_Odd_9", game.Enemy("Char_Odd_9", None, game.Pool(50.0))) == "no_pool" and len(noted) == 1)

    class TwoPools(game.Damage):
        def AddHealthPool(self, **kwargs: object) -> int:
            actor = kwargs["Context"]
            actor.pools[1], actor.pools[2] = game.Pool(10.0), game.Pool(20.0)
            game.give_type(actor, game.SHIELD)
            return 1

    state["classes"]["DamageStatics"] = game.Library("DamageStatics", TwoPools())
    noted.clear()
    split = shields.Shields(announce, refill=False, note=lambda event, **fields: noted.append((event, fields)))
    twice = bandit("Char_Twice_10")
    check("two new pools: no_pool, the pools after written as read", split.give(twice.Name, twice) == "no_pool"
          and noted[0][1]["pools"] == [1000, -1, -1] and noted[0][1]["pools_after"] == [1000, 10, 20])
    game.install(state)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")
    import traceback
    traceback.print_exc()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
