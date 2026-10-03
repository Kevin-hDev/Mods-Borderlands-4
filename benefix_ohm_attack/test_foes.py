"""Tests the foes around: the characters the beam may be thrown at, walked once a second at most."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import foes  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def walks() -> int:
    return sum(1 for name, _exact in state["finds"] if name == "OakCharacter")


def actors() -> list:
    return [foe.actor() for foe in foes.around(character)]


def scene(*others) -> None:
    foes.restart()
    state["all"]["OakCharacter"] = [sdk_stubs.Actor("Default__OakCharacter"), character, *others]


pc, character = sdk_stubs.player(state)
character.K2_GetActorLocation = lambda: types.SimpleNamespace(X=0.0, Y=0.0, Z=50.0)
character.HealthState = types.SimpleNamespace(bCurrentlyDead=False)
psycho = sdk_stubs.Actor("Char_Psycho_4", (1000.0, 0.0, 50.0))
brute = sdk_stubs.Actor("Char_Brute_9", (400.0, 300.0, 50.0))
vendor = sdk_stubs.Actor("Char_NPC_Vendor_3", (100.0, 0.0, 50.0))
familiar = sdk_stubs.Actor("Char_DarkSiren_PhaseFamiliar_2", (200.0, 0.0, 50.0))
corpse = sdk_stubs.Actor("Char_Psycho_14", (300.0, 0.0, 50.0), dead=True)
crate = sdk_stubs.Actor("Crate_7", (50.0, 0.0, 50.0))
state["attitudes"][id(familiar)] = sdk_stubs.ETeamAttitude.friendly

scene(psycho, brute, vendor, familiar, corpse, crate)
check("nobody is walked before somebody asks", walks() == 0 and foes.known() == 0)
found = foes.around(character)
check("the foes are the game's characters that are not the player, not an ally by name, not a thing and not dead, "
      "the nearest to the player first",
      [foe.actor() for foe in found] == [familiar, brute, psycho] and [foe.species for foe in found]
      == ["Char_DarkSiren_PhaseFamiliar", "Char_Brute", "Char_Psycho"] and foes.known() == 3)
check("the characters are walked once, by their class and its children, as the enemy probes do",
      state["finds"] == [("OakCharacter", False)])
check("who is a friend is not asked at the walk", state["attitude_calls"] == [])
check("a foe says whether the game calls it a friend", found[0].friend(character) is True
      and found[1].friend(character) is False)
asked = len(state["attitude_calls"])
found[0].friend(character)
found[1].friend(character)
check("and the game is asked once per character", asked == 2 and len(state["attitude_calls"]) == 2)

for _ in range(19):
    foes.tick(0.05)
    foes.around(character)
check("asked again within the second, the list is the same one: no new walk", walks() == 1 and actors()[1] is brute)
newcomer = sdk_stubs.Actor("Char_Psycho_30", (100.0, 0.0, 50.0))
state["all"]["OakCharacter"].append(newcomer)
check("a character that has just appeared is not known yet", newcomer not in actors())
foes.tick(0.05)
check("a second after the last walk the characters are walked again", actors()[0] is newcomer and walks() == 2)
for _ in range(100):
    foes.tick(0.05)
check("time passing with nobody asking walks nothing", walks() == 2)
foes.around(character)
check("the next asking does", walks() == 3)

state["gone"].add(id(brute))
check("a foe that left the world is in the list until the next walk, and names nobody",
      [foe.actor() for foe in foes.around(character) if foe.species == "Char_Brute"] == [None])
state["gone"].discard(id(brute))

scene(*(sdk_stubs.Actor(f"Char_Rat_{number}", (100.0 * (number + 1), 0.0, 50.0)) for number in range(80)))
check("the list keeps the sixty nearest", foes.known() == 0 and len(foes.around(character)) == foes.MAX_FOES == 60
      and max(foe.actor().at[0] for foe in foes.around(character)) == 6000.0)
scene(*(sdk_stubs.Actor(f"Crate_{number}") for number in range(foes.MAX_PAWNS)), psycho)
check("the walk is bounded: a character past the bound is not seen", actors() == [] and foes.MAX_PAWNS == 400)
scene(types.SimpleNamespace(Name="Char_Broken_1"), psycho)
check("a character that cannot be read is passed over, the others still seen", actors() == [psycho])
del character.K2_GetActorLocation
scene(psycho, brute)
check("a player that cannot be placed leaves the foes in the game's own order", actors() == [psycho, brute])

scene(psycho)
state["all"]["OakCharacter"] = None
errors, walked = len(state["errors"]), walks()
check("a walk the game refuses is nobody around, said once", actors() == [] and len(state["errors"]) == errors + 1)
for _ in range(50):
    foes.tick(0.05)
    foes.around(character)
check("and is not asked for again", walks() == walked + 1 and len(state["errors"]) == errors + 1)
state["all"]["OakCharacter"] = [psycho]
foes.restart()
check("until the mod is switched on anew", actors() == [psycho])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
