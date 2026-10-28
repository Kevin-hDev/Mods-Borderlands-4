"""Saved control choices, key validation and capture/menu constants."""

from mods_base import KeybindOption, SpinnerOption

from . import input_list, report

GAME, SINGLE, DOUBLE = "Game controls", "One key", "Two keys"
MODES = (GAME, SINGLE, DOUBLE)
KEYBOARD, GAMEPAD = "keyboard", "gamepad"
DEVICE_NAMES = {KEYBOARD: "Keyboard / mouse", GAMEPAD: "Controller"}
MAX_CAPTURE_KEYS = 512
INPUT_GAP_NS = 500_000_000
PULSE_KEYS = frozenset(("MouseScrollUp", "MouseScrollDown"))
RESERVED_KEYS = frozenset(("Escape", "Tilde"))
AXIS_KEYS = frozenset(("MouseWheelAxis", "Gamepad_LeftX", "Gamepad_LeftY",
                       "Gamepad_RightX", "Gamepad_RightY"))
RESTORED = "Default settings restored."
FAILED = "Could not save changes. Previous settings kept."


def device_of(key: str) -> str:
    return GAMEPAD if key.startswith("Gamepad_") else KEYBOARD


def catalogue() -> frozenset[str]:
    # Reuse the installed menu's key names; do not maintain a competing list of mouse buttons.
    from console_mod_menu.key_matching import KNOWN_KEYS
    if len(KNOWN_KEYS) > MAX_CAPTURE_KEYS:
        raise ValueError("too many key names")
    return frozenset(key for key in KNOWN_KEYS if isinstance(key, str)
                     and len(key) <= input_list.MAX_NAME_LENGTH and input_list.NAME_PATTERN.fullmatch(key)
                     and key not in AXIS_KEYS and not key.endswith("Axis"))


class Device:
    def __init__(self, name: str) -> None:
        self.name = name
        self.mode = SpinnerOption(f"{name}_mode", GAME, list(MODES), is_hidden=True)
        self.first = KeybindOption(f"{name}_first", None, is_hidden=True)
        self.second = KeybindOption(f"{name}_second", None, is_hidden=True)
        self.options = (self.mode, self.first, self.second)

    def selection(self) -> tuple[str, ...] | None:
        if self.mode.value == GAME:
            return None
        if self.mode.value not in (SINGLE, DOUBLE):
            raise ValueError("invalid control mode")
        result = (self.first.value,) if self.mode.value == SINGLE else (self.first.value, self.second.value)
        valid = catalogue() - RESERVED_KEYS
        if any(type(key) is not str or key not in valid or device_of(key) != self.name for key in result):
            raise ValueError("invalid control key")
        if len(result) == 2 and (result[0] == result[1] or any(key in PULSE_KEYS for key in result)):
            raise ValueError("invalid held combination")
        return result


DEVICES = (Device(KEYBOARD), Device(GAMEPAD))
ALL = tuple(option for device in DEVICES for option in device.options)


def groups(mappings: list) -> tuple[tuple[str, ...], ...]:
    defaults = input_list.grapple_keys(mappings)
    result = []
    for device in DEVICES:
        try:
            chosen = device.selection()
        except (ValueError, ImportError):
            report.error_once(f"controls:{device.name}", "invalid controls; using the game's controls")
            chosen = None
        result.extend((chosen,) if chosen else ((key,) for key in sorted(defaults)
                                               if device_of(key) == device.name))
    return tuple(result)
