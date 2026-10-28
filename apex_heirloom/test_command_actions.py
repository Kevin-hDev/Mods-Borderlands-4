"""Tests the COMMANDS page's saves, Apex Movement's: a key assigned is saved to its option and its bind at once;
refused, it keeps the previous key and its cause for the window's words, the console's keys included; a save the disk
refuses puts every key back; the defaults put the put-away keys back and clear the inspection's."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import panel_fixture as pf  # noqa: E402

from apex_heirloom import inspect_keys, keys, mod  # noqa: E402
from apex_heirloom.command_actions import Actions  # noqa: E402
from apex_heirloom.command_keys import KEYS  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


actions = Actions(KEYS, mod)
saves = pf.state["settings_saves"]
check("a key assigned is saved to its option and its bind", actions.assign("inspect", "keyboard", "F")
      and inspect_keys.keyboard_key.value == "F" and inspect_keys.keyboard_bind.key == "F"
      and actions.last_status == "saved" and pf.state["settings_saves"] == saves + 1)
check("a controller button too", actions.assign("inspect", "controller", "Gamepad_DPad_Up")
      and inspect_keys.controller_bind.key == "Gamepad_DPad_Up")
put_away = keys.keyboard_key.value
check("the inspection's key refused for putting away, which keeps its own and says why",
      not actions.assign("put_away", "keyboard", "F") and keys.keyboard_key.value == put_away
      and actions.last_status == "duplicate_inspect")
check("the wheel refused, the previous key kept", not actions.assign("inspect", "keyboard", "MouseScrollUp")
      and inspect_keys.keyboard_key.value == "F" and actions.last_status == "wheel_key")
check("the console's key refused before anything is saved", not actions.assign("inspect", "keyboard", "F10")
      and inspect_keys.keyboard_key.value == "F" and actions.last_status == "reserved_key")
check("an unknown command refused", not actions.assign("reload", "keyboard", "R")
      and actions.last_status == "refused")
check("a key cleared: none", actions.assign("inspect", "keyboard", None) and inspect_keys.keyboard_key.value is None
      and inspect_keys.keyboard_bind.key is None)
pf.state["refuse_saves"] = True
check("a save the disk refuses keeps the previous key and says it failed",
      not actions.assign("inspect", "keyboard", "G") and inspect_keys.keyboard_key.value is None
      and inspect_keys.keyboard_bind.key is None and actions.last_status == "failed")
pf.state["refuse_saves"] = False
keys.controller_key.value = "Gamepad_FaceButton_Top"
check("the defaults put the put-away keys back and leave no inspection key",
      actions.defaults() and keys.keyboard_key.value == keys.keyboard_bind.default_key
      and keys.controller_bind.key == "Gamepad_FaceButton_Left"
      and inspect_keys.keyboard_key.value is None and inspect_keys.controller_key.value is None
      and inspect_keys.controller_bind.key is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
