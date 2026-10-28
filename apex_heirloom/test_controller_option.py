"""Tests the key checks: a controller button for the controller's option, a keyboard or mouse key for the keyboard's."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import heirloom_stubs  # noqa: E402

heirloom_stubs.install()

from apex_heirloom import keys  # noqa: E402
from apex_heirloom.controller_option import ControllerKeybindOption, normalize_controller_key, normalize_key  # noqa: E402
from apex_heirloom.key_option import ControllerKeybindOption as SharedControllerOption  # noqa: E402
from apex_heirloom.key_option import normalize_controller_key as shared_controller_key  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def refused(check_key, value) -> bool:
    try:
        check_key(value)
    except ValueError:
        return True
    return False


check("a controller button is kept", normalize_controller_key("Gamepad_FaceButton_Left") == "Gamepad_FaceButton_Left")
check("the generated shared option is the only controller authority",
      ControllerKeybindOption is SharedControllerOption and normalize_controller_key is shared_controller_key)
check("no button is a valid empty value", normalize_controller_key(None) is None and normalize_controller_key("None") is None)
check("a keyboard key is refused", refused(normalize_controller_key, "A"))
check("a stick or trigger as an axis is refused",
      all(refused(normalize_controller_key, name) for name in ("Gamepad_LeftX", "Gamepad_Right2D",
                                                               "Gamepad_LeftTriggerAxis")))
check("a malformed name is refused",
      all(refused(normalize_controller_key, value) for value in ("Gamepad_", "Gamepad_A B", 3, "Gamepad_" + "x" * 80)))
check("the window checks the controller's option as a button", normalize_key(keys.controller_key, "Gamepad_DPad_Up")
      == "Gamepad_DPad_Up" and refused(lambda value: normalize_key(keys.controller_key, value), "Q"))
check("the window checks the keyboard's option as a key", normalize_key(keys.keyboard_key, "Q") == "Q"
      and refused(lambda value: normalize_key(keys.keyboard_key, value), "Gamepad_DPad_Up"))
check("the controller's option is shown once, in the SDK's menu", keys.controller_key.is_hidden is False)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
