"""Tests the rules on the COMMANDS page's keys: each card's row sets its own option, the defaults put the put-away
keys back and leave the inspection none, and a key is refused, with its cause, when another command holds it on the
same device, when it is the wheel on a keyboard's row, a key of the wrong device, or the console's."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import panel_fixture as pf  # noqa: E402

from apex_heirloom import command_keys, control_reserved, inspect_keys, keys  # noqa: E402
from apex_heirloom.command_keys import KEYS, Refused  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def refusal(changes) -> str:
    """The cause a change is refused for, "" when it is not, "error" for a plain ValueError."""
    try:
        KEYS.validate(changes)
    except Refused as error:
        return error.status
    except ValueError:
        return "error"
    return ""


check("each card's row names its own option", KEYS.identifier("put_away", "keyboard") == "put_away_keyboard"
      and KEYS.identifier("put_away", "controller") == "put_away_controller"
      and KEYS.identifier("inspect", "keyboard") == "inspect_keyboard"
      and KEYS.identifier("inspect", "controller") == "inspect_controller")
try:
    KEYS.identifier("reload", "keyboard")
    unknown = False
except ValueError:
    unknown = True
check("an unknown command is refused", unknown)
check("the four keys' options, in the page's order",
      KEYS.options == (keys.keyboard_key, keys.controller_key, inspect_keys.keyboard_key, inspect_keys.controller_key))
check("the defaults: the put-away keys' own, no inspection key", KEYS.defaults() == {
    "put_away_keyboard": keys.keyboard_bind.default_key, "put_away_controller": "Gamepad_FaceButton_Left",
    "inspect_keyboard": None, "inspect_controller": None})

keys.keyboard_key.value, keys.controller_key.value = "Q", "Gamepad_FaceButton_Left"
inspect_keys.keyboard_key.value = inspect_keys.controller_key.value = None
check("a free key is kept as it is", KEYS.validate({"inspect_keyboard": "F"}) == {"inspect_keyboard": "F"})
check("the key that puts the weapon away is refused for the inspection, on the keyboard",
      refusal({"inspect_keyboard": "Q"}) == "duplicate_put_away")
check("... and on the controller", refusal({"inspect_controller": "Gamepad_FaceButton_Left"}) == "duplicate_put_away")
inspect_keys.keyboard_key.value = "F"
check("the inspection's key is refused for putting away", refusal({"put_away_keyboard": "F"}) == "duplicate_inspect")
check("a button no command holds is kept on the controller, whatever the keyboard's keys",
      refusal({"inspect_controller": "Gamepad_FaceButton_Top"}) == "")
check("two commands given one key in the same change are refused",
      refusal({"put_away_keyboard": "G", "inspect_keyboard": "G"}) != "")
check("no key twice is no duplicate", refusal({"put_away_keyboard": None, "inspect_keyboard": None}) == "")
check("the key a command holds may be given to it again", refusal({"inspect_keyboard": "F"}) == "")
check("the wheel is refused on both keyboard rows, up and down",
      refusal({"put_away_keyboard": "MouseScrollUp"}) == "wheel_key"
      and refusal({"inspect_keyboard": "MouseScrollDown"}) == "wheel_key")
check("a controller button on a keyboard row, or a key on a controller row, is refused as the row's",
      refusal({"inspect_keyboard": "Gamepad_DPad_Up"}) == "invalid_keyboard"
      and refusal({"inspect_controller": "F"}) == "invalid_controller"
      and refusal({"put_away_keyboard": "LeftMouseButton"}) == "invalid_keyboard")
check("an unknown option or an empty change is refused",
      refusal({"reload_keyboard": "R"}) == "error" and refusal({}) == "error" and refusal(["F"]) == "error")

KEYS.set_values({"inspect_controller": "Gamepad_DPad_Up"})
check("set, a key reaches its option and its bind", inspect_keys.controller_key.value == "Gamepad_DPad_Up"
      and inspect_keys.controller_bind.key == "Gamepad_DPad_Up")
inspect_keys.controller_bind.key = keys.keyboard_bind.key = "LeftMouseButton"
KEYS.align()
check("aligned, each bind takes its option's key", inspect_keys.controller_bind.key == "Gamepad_DPad_Up"
      and keys.keyboard_bind.key == "Q")

check("a captured console key is refused, the configured one and Tilde, Escape too",
      KEYS.refusal("F10") == "reserved_key" and KEYS.refusal("Tilde") == "reserved_key"
      and KEYS.refusal("Escape") == "reserved_key")
check("any other key, or none, passes", KEYS.refusal("F") is None and KEYS.refusal(None) is None)


def unreadable():
    raise RuntimeError("no input settings")


shipped = control_reserved.console_keys
control_reserved.console_keys = unreadable
check("a key whose conflict with the console cannot be checked is refused as a failed save, said once",
      command_keys.KEYS.refusal("F") == "failed" and command_keys.KEYS.refusal("G") == "failed"
      and sum("console shortcuts" in line for line in pf.state["errors"]) == 1)
control_reserved.console_keys = shipped

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
