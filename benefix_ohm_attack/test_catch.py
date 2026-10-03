"""Tests the catch: the foe near the aim's line the beam goes to when the aim itself is on nobody."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import aim, catch, foes  # noqa: E402

fails: list[str] = []
REACH = 5000.0


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(found, wanted):
    return all(abs(a - b) < 1e-6 for a, b in zip(found, wanted))


def walks() -> int:
    return sum(1 for name, _exact in state["finds"] if name == "OakCharacter")


def caught(width: float, reach: float = REACH) -> aim.Aim:
    """One frame: the aim of the moment, then what the catch makes of it."""
    return catch.near(pc, character, aim.look(pc, character, reach), width, reach)


def scene(*standing, balls=(), look=(0.0, 5.0)) -> None:
    """A new session in a new world: the characters the game holds, each a ball 40 cm wide, and where the camera
    looks. Five degrees aside, the aim passes 87 cm from the middle of an enemy 10 m ahead."""
    foes.restart()
    catch.restart()
    state["look"] = look
    state["all"]["OakCharacter"] = [character, *standing]
    sdk_stubs.world(state, *((actor, 40.0) for actor in standing), *balls)


pc, character = sdk_stubs.player(state)
psycho = sdk_stubs.Actor("Char_Psycho_4", (1000.0, 0.0, 50.0))
brute = sdk_stubs.Actor("Char_Brute_9", (1000.0, 150.0, 50.0))

scene(psycho)
plain = aim.look(pc, character, REACH)
check("the aim passes beside him: it is on nobody", plain.enemy is None and plain.caught is False)
check("a catch distance of nothing changes nothing, and the game's characters are not walked",
      catch.near(pc, character, plain, 0.0, REACH) is plain and walks() == 0)
check("a foe farther from the aim's line than the catch distance is not caught: his body, 30 cm about his middle, "
      "is 57 cm away", caught(50.0).enemy is None and caught(50.0).hidden is False)
taken = caught(60.0)
check("one within it is: the beam ends where the way to his middle meets him", taken.enemy is psycho
      and near(taken.anchor, (960.0, 0.0, 50.0)) and taken.species == "Char_Psycho" and taken.distance == 960.0)
check("the aim says he was caught, and carries the game's answer for the hits",
      taken.caught is True and aim.hit_actor(taken.hit) is psycho)
check("the characters are walked once for all these frames", walks() == 1)

scene(psycho, look=(6.0, 0.0))
check("a body is as tall as a man: the aim passing a metre above his middle catches him within 20 cm",
      caught(20.0).enemy is psycho and caught(10.0).enemy is None)
scene(psycho, look=(-6.0, 0.0))
check("and the same below", caught(20.0).enemy is psycho and caught(10.0).enemy is None)

scene(psycho, look=(0.0, 175.0))
check("a foe behind the player is not caught, however wide the catch", caught(500.0).enemy is None)
scene(psycho)
check("nor one past the beam's reach", caught(100.0, reach=500.0).enemy is None)

scene(psycho, brute)
check("of two within the distance, the one nearest the aim's line is caught", caught(100.0).enemy is brute)
state["attitudes"][id(brute)] = sdk_stubs.ETeamAttitude.friendly
scene(psycho, brute)
check("a friend is never caught: the next one is", caught(100.0).enemy is psycho)
del state["attitudes"][id(brute)]
scene(psycho, brute)
caught(100.0)
brute.HealthState.bCurrentlyDead = True
check("a foe that died since the walk is not caught", caught(100.0).enemy is psycho)
brute.HealthState.bCurrentlyDead = False
state["gone"].add(id(brute))
check("nor one that left the world", caught(100.0).enemy is psycho)
state["gone"].discard(id(brute))

wall = sdk_stubs.Actor("StaticMeshActor_1", (500.0, 0.0, 50.0))
scene(psycho, balls=((wall, 30.0),))
behind = caught(100.0)
check("a foe hidden behind a wall is not caught: the aim stays where it was, and says somebody was hidden",
      behind.enemy is None and behind.hidden is True and behind.anchor == aim.look(pc, character, REACH).anchor)

row = [sdk_stubs.Actor(f"Char_Rat_{number}", (1000.0 + 100.0 * number, -200.0 - 20.0 * number, 50.0))
       for number in range(3)]
seen = sdk_stubs.Actor("Char_Psycho_8", (1000.0, 100.0, 50.0))
cover = sdk_stubs.Actor("StaticMeshActor_2", (500.0, -100.0, 50.0))
scene(*row, seen, balls=((cover, 60.0),), look=(0.0, -11.31))
rays = len(state["rays"])
check("the ways to three hidden foes are tried, no more: a fourth one in the open, farther from the aim, is not "
      "looked for this frame", caught(400.0).enemy is None and len(state["rays"]) == rays + 1 + catch.MAX_TRIED)
scene(*row[:2], seen, balls=((cover, 60.0),), look=(0.0, -11.31))
check("with two hidden he is caught", caught(400.0).enemy is seen)

scene(psycho)
world_line = state["line"]


def broken(start, end):
    raise RuntimeError("the game refuses this ray")


plain = aim.look(pc, character, REACH)
state["line"] = broken
errors = len(state["errors"])
check("a catch that fails does not take the shot down: the aim stands, said once",
      catch.near(pc, character, plain, 100.0, REACH) is plain and len(state["errors"]) == errors + 1)
state["line"] = world_line
check("and nobody is caught again", caught(100.0).enemy is None and len(state["errors"]) == errors + 1)
catch.restart()
check("until the mod is switched on anew", caught(100.0).enemy is psycho)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
