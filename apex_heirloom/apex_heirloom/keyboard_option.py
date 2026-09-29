"""The keyboard key's persisted option: the camera runtime's keyboard shortcut (key_option.py), without the wheel.

The wheel's notch comes as a press and a release in the same frame, so it is never held; and the game changes weapon
with it, so a press would put one weapon away while drawing the next (audit, 2026-09-25).
"""

from typing import Any

from .key_option import KeyboardKeybindOption, normalize_keyboard_key

_WHEEL = frozenset(("MouseScrollUp", "MouseScrollDown"))


def normalize_put_away_key(value: Any) -> str | None:
    key = normalize_keyboard_key(value)
    if key in _WHEEL:
        raise ValueError("invalid keyboard key")
    return key


class PutAwayKeyOption(KeyboardKeybindOption):
    """KeyboardKeybindOption which also unbinds the wheel, typed in the SDK's menu or loaded from disk."""

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "value":
            try:
                value = normalize_put_away_key(value)
            except ValueError:
                value = None
        super().__setattr__(name, value)
