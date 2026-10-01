"""A keyboard key's persisted option: the camera runtime's keyboard shortcut (key_option.py), without the wheel. Both
keyboard keys of the mod take it: the one that puts the weapon away (keys.py) and the one that inspects the heirloom
(inspect_keys.py).

The wheel's notch comes as a press and a release in the same frame, so it is never held; and the game changes weapon
with it, so a press would put one weapon away while drawing the next (audit, 2026-09-25).
"""

from typing import Any

from .key_option import KeyboardKeybindOption, normalize_keyboard_key

WHEEL = frozenset(("MouseScrollUp", "MouseScrollDown"))


def normalize_wheel_free_key(value: Any) -> str | None:
    key = normalize_keyboard_key(value)
    if key in WHEEL:
        raise ValueError("invalid keyboard key")
    return key


class WheelFreeKeyOption(KeyboardKeybindOption):
    """KeyboardKeybindOption which also unbinds the wheel, typed in the SDK's menu or loaded from disk."""

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "value":
            try:
                value = normalize_wheel_free_key(value)
            except ValueError:
                value = None
        super().__setattr__(name, value)
