"""Tests what the mod reads of a character of the game: where it stands, whether it is dead, whether it is a friend."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import enemy  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


pc, character = sdk_stubs.player(state)
psycho = sdk_stubs.Actor("Char_Psycho_4", (100.0, 200.0, 30.0))
check("where a character stands is its own location", enemy.place(psycho) == (100.0, 200.0, 30.0))
errors = len(state["errors"])
check("one that cannot say where it stands is nowhere, and it is no error: it may just have left the world",
      enemy.place(types.SimpleNamespace(Name="Char_Psycho_5")) is None and len(state["errors"]) == errors)
psycho.at = (float("nan"), 0.0, 0.0)
check("a place that is no number is nowhere", enemy.place(psycho) is None)
psycho.at = (100.0, 200.0, 30.0)

check("a living character is not dead, a dead one is",
      not enemy.dead(psycho) and enemy.dead(sdk_stubs.Actor("Char_Psycho_6", dead=True)))
check("a character whose death cannot be read counts as alive, said once",
      not enemy.dead(types.SimpleNamespace(Name="Char_Psycho_7")) and len(state["errors"]) == errors + 1
      and not enemy.dead(types.SimpleNamespace(Name="Char_Psycho_8")) and len(state["errors"]) == errors + 1)

lines = len(state["log"])
check("a character the game calls hostile is no friend", not enemy.friend(character, psycho))
check("the game is asked what the player is to that character", state["attitude_calls"] == [(character, psycho)])
check("the first asking of a session is written before it is made, and its answer after",
      state["log"][lines:] == ["[Benefix Ohm Attack] first attitude asked, towards Char_Psycho",
                               "[Benefix Ohm Attack] the game answered <ETeamAttitude.hostile: 2>"])
familiar = sdk_stubs.Actor("Char_DarkSiren_PhaseFamiliar_2")
state["attitudes"][id(familiar)] = sdk_stubs.ETeamAttitude.friendly
check("one the game calls friendly is a friend: the player's own familiar", enemy.friend(character, familiar))
check("only the first asking is written", len(state["log"]) == lines + 2)
state["attitudes"][id(familiar)] = sdk_stubs.ETeamAttitude.neutral
check("a neutral one is no friend: it may be shot at", not enemy.friend(character, familiar))
state["attitudes"][id(familiar)] = 0
check("an answer given as a plain number is read by the game's own order, 0 being friendly",
      enemy.friend(character, familiar))
state["attitudes"][id(familiar)] = types.SimpleNamespace(name="Friendly")
check("an answer's name is read whatever its capitals", enemy.friend(character, familiar))

state["attitude_raises"] = TypeError("two arguments expected")
errors, asked = len(state["errors"]), len(state["attitude_calls"])
check("a game that will not say: nobody is a friend, said once", not enemy.friend(character, familiar)
      and len(state["errors"]) == errors + 1)
enemy.friend(character, familiar)
check("and it is not asked again", len(state["attitude_calls"]) == asked + 1 and len(state["errors"]) == errors + 1)
state["attitude_raises"] = None
enemy.forget()
check("until the mod is switched on anew", len(state["attitude_calls"]) == asked + 1
      and enemy.friend(character, familiar) and len(state["attitude_calls"]) == asked + 2)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
