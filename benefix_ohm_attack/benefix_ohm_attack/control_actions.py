# Generated: the settings window Kevin's mods share, taken from Apex Heirloom's and put under this mod's names.
# Its comments may speak of that mod. Never edited by hand: the window's generator writes this file.
"""Saves option values all together or not at all: a key chosen on the CONTROLS page, the window's Restore and Undo."""

from typing import Any

from . import report


def save_values(mod: Any, values: tuple) -> bool:
    old = tuple((option, option.value) for option, _ in values)
    try:
        for option, value in values:
            option.value = value
        mod.save_settings()
    except Exception:
        for option, value in old:
            option.value = value
        try:
            mod.save_settings()
        except Exception:
            report.error_once("controls:save", "settings could not be saved; retry before leaving the game")
        return False
    return True
