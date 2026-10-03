"""Tests the bounce: from the enemy the beam is on, a second beam to the nearest living foe within reach, taken from
the foes known, kept while it stays near, alive and in the world."""

import math
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import beam, bounce, foes, lock  # noqa: E402

fails: list[str] = []
FIRE = beam.Effect(sdk_stubs.FIRE_BEAM)
SPOT = (960.0, 0.0, 50.0)


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def first_on(actor, spot=SPOT):
    return lock.Target(actor, spot, "the first's answer", "Char_Psycho", 960.0, True)


def frame(first):
    foes.tick(0.05)
    return bounce.follow(character, first, FIRE)


def frames(first, seconds: float):
    found = None
    for _ in range(round(seconds / 0.05)):
        found = frame(first)
    return found


def walks() -> int:
    return sum(1 for name, _exact in state["finds"] if name == "OakCharacter")


def removed() -> int:
    return state["events"].count("REMOVED")


def scene(*others, balls=()):
    """A new session in a new world: the characters the game holds, the player and the first enemy among them."""
    foes.restart()
    bounce.restart()
    state["all"]["OakCharacter"] = [sdk_stubs.Actor("Default__OakCharacter"), character, psycho, *others]
    standing = (actor for actor in others if isinstance(actor, sdk_stubs.Actor))
    sdk_stubs.world(state, (psycho, 40.0), *((actor, 40.0) for actor in standing), *balls)


pc, character = sdk_stubs.player(state)
# The player stands beside the first enemy, and reads as any character does: nearer than everyone, never chosen.
character.K2_GetActorLocation = lambda: types.SimpleNamespace(X=1000.0, Y=60.0, Z=50.0)
character.HealthState = types.SimpleNamespace(bCurrentlyDead=False)
psycho = sdk_stubs.Actor("Char_Psycho_4", (1000.0, 0.0, 50.0))
brute = sdk_stubs.Actor("Char_Brute_9", (1000.0, 500.0, 50.0))
farther = sdk_stubs.Actor("Char_Psycho_12", (1000.0, -900.0, 50.0))
too_far = sdk_stubs.Actor("Char_Psycho_13", (1000.0, 2500.0, 50.0))
vendor = sdk_stubs.Actor("Char_NPC_Vendor_3", (1000.0, 100.0, 50.0))
familiar = sdk_stubs.Actor("Char_DarkSiren_PhaseFamiliar_2", (1000.0, 200.0, 50.0))
corpse = sdk_stubs.Actor("Char_Psycho_14", (1000.0, 300.0, 50.0), dead=True)
crate = sdk_stubs.Actor("Crate_7", (1000.0, 50.0, 50.0))
state["attitudes"][id(familiar)] = sdk_stubs.ETeamAttitude.friendly

scene(brute, farther, too_far, vendor, familiar, corpse, crate)
check("with no enemy under the beam there is no bounce, and the game's characters are not walked",
      frame(None) is None and walks() == 0 and state["spawns"] == [])
logged = len(state["log"])
second = frame(first_on(psycho))
check("the bounce goes to the nearest living foe within 20 m of the spot the beam is on: not the first enemy, not "
      "the player, not an ally, not a friend, not a corpse, not a thing",
      second is not None and second.enemy is brute and second.species == "Char_Brute")
reach = math.dist(SPOT, brute.at)
check("its beam ends on the second enemy's skin, on the side of the first",
      abs(math.dist(second.point, brute.at) - 40.0) < 1e-6 and abs(math.dist(SPOT, second.point) - (reach - 40.0)) < 1e-6)
check("the game's answer for the hits is the ray's that met him", sdk_stubs.spot(second.hit.ImpactPoint) == second.point)
check("the characters are walked once, by the foes' list", state["finds"] == [("OakCharacter", False)])
check("the game is asked who is a friend only of those nearer than the one already found",
      [actor for _player, actor in state["attitude_calls"]] == [familiar, brute])
made = state["beams"][-1]
check("a second beam is lit from the spot on the first enemy to the second, of the shot's element",
      len(state["spawns"]) == 1 and state["spawns"][0][1] == "the fire beam" and state["spawns"][0][2] == SPOT
      and made.targets == [("User.Target", second.point)])
check("the log says who and how far from the first", state["log"][logged:] == [
    "[Benefix Ohm Attack] first attitude asked, towards Char_DarkSiren_PhaseFamiliar",
    "[Benefix Ohm Attack] the game answered <ETeamAttitude.friendly: 0>",
    "[Benefix Ohm Attack] bounce on Char_Brute, 5 m from the first"])

frames(first_on(psycho), 2.0)
check("while he is held nobody is looked for: no walk, no new beam", walks() == 1 and len(state["spawns"]) == 1)
moved = frame(first_on(psycho, (960.0, 20.0, 60.0)))
check("the beam follows both of its ends", made.poses[-1][0] == (960.0, 20.0, 60.0) and made.targets[-1][1] == moved.point)

brute.at = (1000.0, 2300.0, 50.0)
check("between 20 and 25 m he is kept: the bounce is taken within 20 m and let go past 25", frame(first_on(psycho)).enemy is brute)
brute.at = (1000.0, 2600.0, 50.0)
gone, lines = removed(), len(state["log"])
replaced = frame(first_on(psycho))
check("past 25 m he is let go and his beam removed; the next nearest is found in the same frame and a beam lit "
      "for him", replaced.enemy is farther and removed() == gone + 1 and len(state["spawns"]) == 2)
check("the log says a shot's first bounce only", len(state["log"]) == lines)
farther.HealthState.bCurrentlyDead = True
check("he dies: he is let go", frame(first_on(psycho)) is None and removed() == gone + 2)
walked = walks()
frames(first_on(psycho), 0.9)
check("with nobody to bounce on, the foes are looked through at every frame and walked no more than once a second",
      walks() == walked)
farther.HealthState.bCurrentlyDead = False
state["gone"].add(id(farther))
check("he leaves the world: he is not bounced on", frame(first_on(psycho)) is None)
state["gone"].discard(id(farther))
check("he is back: he is found at once", frame(first_on(psycho)).enemy is farther)

brute.at = (1000.0, 500.0, 50.0)
scene(brute)
check("a session's first frame on an enemy looks for the bounce at once", frame(first_on(psycho)).enemy is brute)
on_brute = first_on(brute, (1000.0, 460.0, 50.0))
check("the beam moves to the second enemy: he is the first now, and the old first is the bounce in his turn",
      frame(on_brute).enemy is psycho)
gone = removed()
bounce.forget()
check("a shot's end lets everyone go and removes the beam", removed() == gone + 1 and frame(None) is None)
walked, lines = walks(), len(state["log"])
check("the next shot bounces at once on the foes already known, without a new walk: tapping the key is no way to "
      "walk the characters at every press", frame(first_on(psycho)).enemy is brute and walks() == walked)
check("it says its own first bounce",
      state["log"][lines:] == ["[Benefix Ohm Attack] bounce on Char_Brute, 5 m from the first"])

scene()
walked, lit = walks(), len(state["spawns"])
check("with nobody around there is no bounce", frames(first_on(psycho), 3.0) is None and len(state["spawns"]) == lit)
check("and the characters are walked once a second, not at every frame", walks() == walked + 3)

wall = sdk_stubs.Actor("StaticMeshActor_1", (990.0, 430.0, 50.0))
scene(brute, balls=((wall, 30.0),))
hidden = frame(first_on(psycho))
check("a second enemy the last ray does not meet is still the bounce: the beam ends at his middle, and the hit has "
      "no ray's answer to give", hidden.enemy is brute and hidden.point == brute.at and hidden.hit is None)

scene(brute)
world_line = state["line"]


def broken(start, end):
    raise RuntimeError("the game refuses this ray")


state["line"] = broken
errors, gone = len(state["errors"]), removed()
check("a bounce that fails does not take the shot down: no second enemy, no beam left, said once",
      frame(first_on(psycho)) is None and len(state["errors"]) == errors + 1 and removed() == gone
      and len(state["spawns"]) == len(state["beams"]))
state["line"] = world_line
check("and nobody is bounced on again", frames(first_on(psycho), 2.5) is None and len(state["errors"]) == errors + 1)
bounce.restart()
check("until the mod is switched on anew", frame(first_on(psycho)).enemy is brute)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
