"""Checks the shared keyboard/mouse and controller key validators."""

import pathlib
import sys
import types


class FakeKeybindOption:
    @classmethod
    def from_keybind(cls, bind):
        option = cls()
        option.identifier = bind.identifier
        option.value = bind.key
        option.default_value = bind.key
        option.is_hidden = bind.is_hidden
        return option


mods_base = types.ModuleType("mods_base")
mods_base.KeybindOption = FakeKeybindOption
sys.modules["mods_base"] = mods_base
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from apex_camera_runtime.key_option import (  # noqa: E402
    ControllerKeybindOption,
    KeyboardKeybindOption,
    normalize_controller_key,
    normalize_keyboard_key,
)


def refused(fn, value):
    try:
        fn(value)
    except ValueError:
        return True
    return False


assert normalize_keyboard_key(None) is None
assert normalize_keyboard_key("") is None
assert normalize_keyboard_key("None") is None
assert normalize_keyboard_key("Six") == "Six"
assert normalize_keyboard_key("ThumbMouseButton") == "ThumbMouseButton"
for value in ("Gamepad_FaceButton_Top", "MouseX", "MouseWheelAxis", "Escape", "Tilde",
              "LeftMouseButton", "bad key", 7):
    assert refused(normalize_keyboard_key, value), value

assert normalize_controller_key(None) is None
assert normalize_controller_key("") is None
assert normalize_controller_key("None") is None
assert normalize_controller_key("Gamepad_FaceButton_Top") == "Gamepad_FaceButton_Top"
for value in ("Six", "Gamepad_LeftX", "Gamepad_RightY", "Gamepad_Left2D",
              "Gamepad_RightTriggerAxis", "Gamepad_bad-key", 7):
    assert refused(normalize_controller_key, value), value

assert issubclass(KeyboardKeybindOption, FakeKeybindOption)
assert issubclass(ControllerKeybindOption, FakeKeybindOption)
print("RESULTAT: OK | keyboard/mouse and controller keys have one shared device validator")
