"""A persisted keyboard or mouse key; controller buttons stay available to the game."""

import re
from typing import Any

from mods_base import KeybindOption

_KEY_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
# The left button fires the weapon and clicks through menus: as the shortcut it would switch views on every shot
# (Kevin, 2026-09-25).
_RESERVED = frozenset(("Escape", "Tilde", "MouseX", "MouseY", "MouseWheelAxis", "LeftMouseButton"))


def normalize_keyboard_key(value: Any) -> str | None:
    if value is None or value in ("", "None"):
        return None
    if (type(value) is not str or not _KEY_NAME.fullmatch(value)
            or value.startswith("Gamepad_") or value.endswith("Axis") or value in _RESERVED):
        raise ValueError("invalid keyboard key")
    return value


class KeyboardKeybindOption(KeybindOption):
    """KeybindOption which safely unbinds malformed or controller values loaded from disk."""

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "value":
            try:
                value = normalize_keyboard_key(value)
            except ValueError:
                value = None
        super().__setattr__(name, value)
