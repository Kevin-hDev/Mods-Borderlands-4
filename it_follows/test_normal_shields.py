"""Tests the normal mode's shields (normal/shields.py) on the health fixture: one given to an enemy without, 40 % of its
health, announced before; none to one with the game's own, nor twice; past GIVEN_MOST refused; a failure said, the
enemy left without. Predator's broken shield refilled REFILL_AFTER_S after it broke, not before, over 1/REFILL_RATE s,
once at a time, again when broken after; a shield holding resets the wait; Bandit's and Senior's never refilled.
Taken off the living; one dead or away only remembered, never called on; an enemy met again under that name still
holding the shield given taken back as given, one whose shield differs left as the game's; the bodies remembered
bounded."""

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
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")
    import traceback
    traceback.print_exc()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
