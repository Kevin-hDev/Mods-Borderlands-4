"""Tests reading the game's key list: finding the grapple by its name, and writing the list down once."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import input_list  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


mappings = state["mappings"]

check("each action is named once, in the game's own order",
      input_list.action_names(mappings) == ["Action_Melee", "Action_Jump_HoldToGlide"])
# Borderlands 4 has no grapple action at all: its 49 actions were read from the game on 2026-09-20
# and not one carries the word. The grapple is the melee button, and that is what the mod takes.
check("with no grapple action in the game, the melee action is taken",
      input_list.grapple_actions(mappings) == ("Action_Melee",))
check("every key bound to it comes back", input_list.grapple_keys(mappings) == {"V", "Gamepad_RightThumbstick"})
check("so does the jump's", input_list.jump_keys(mappings) == {"SpaceBar", "Gamepad_FaceButton_Bottom"})

# The name is not established in Borderlands 4, so the search must not depend on its exact spelling.
other = [sdk_stubs.mapping("Action_GrappleGrabber_Hold", "F"), sdk_stubs.mapping("Action_Reload", "R")]
check("a longer name carrying the word is found too", input_list.grapple_actions(other) ==
      ("Action_GrappleGrabber_Hold",))
check("and a name that does not carry it is left alone", "Action_Reload" not in input_list.grapple_actions(other))
check("the case does not matter", input_list.grapple_actions([sdk_stubs.mapping("Action_GRAPPLE", "G")]) ==
      ("Action_GRAPPLE",))
check("a list with nothing in it gives nothing", input_list.grapple_actions([]) == ())

# If a game update ever names a grapple action, it is the better one and wins over melee.
both = [sdk_stubs.mapping("Action_Melee", "V"), sdk_stubs.mapping("Action_Grapple", "G")]
check("a real grapple action wins over melee", input_list.grapple_actions(both) == ("Action_Grapple",))
check("and melee keeps the punch to itself then", input_list.grapple_keys(both) == {"G"})
check("a game with neither takes nothing",
      input_list.grapple_actions([sdk_stubs.mapping("Action_Reload", "R")]) == ())

input_list.reset()
state["misc"].clear()
input_list.tell_once(mappings)
input_list.tell_once(mappings)
check("the game's whole list is written down, once",
      sum("the game lists 2 actions" in line for line in state["misc"]) == 1)
check("with the actions named", any("Action_Melee, Action_Jump_HoldToGlide" in line for line in state["misc"]))
check("and the keys the grapple sits on", any("Gamepad_RightThumbstick, V" in line for line in state["misc"]))

input_list.reset()
state["warnings"].clear()
input_list.tell_once([sdk_stubs.mapping("Action_Reload", "R")])
check("a game with neither action says so instead of going quiet",
      any("neither a grapple nor a melee action" in line for line in state["warnings"]))

input_list.reset()
state["misc"].clear()
input_list.tell_once([])
check("an empty list is not taken as the answer; it is asked again later", not state["misc"])
input_list.tell_once(mappings)
check("and the real list is written when it turns up", any("the game lists" in line for line in state["misc"]))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
