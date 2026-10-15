"""The key that opens It Follows' window in game, F5 unless the player chose another on the OPTIONS page (decision 48:
« comme pour BL4 Arena, et ce sera F5 par défaut »). Its one authority is a hidden option of the settings file,
written through the window's settings transaction; the SDK's keybind is given its key from it (align), at start and
whenever the window polls. Taken from BL4 Arena's open_key.py, as It Follows keeps its own code (decision 45): a
fault found in one is mended in the other.

The window it opens closes with it too, read as Windows sees it, as Escape is (control_escape.py), when its Unreal
name has a Windows key (control_console_keys.KEY_NAMES); with another key, Escape and CLOSE close it. Opened on the
press: the release then reaches the window, never the game, and the watch waits for the key to be up first
(closer)."""

import re

from mods_base import HiddenOption, keybind

from . import control_console_keys, report
from .control_escape import EscapeWatch

DEFAULT = "F5"
# Never a shortcut: Escape closes the window and cancels a choice; the left button is a click on the menu, which the
# key's field reports when it is clicked a second time.
REFUSED = frozenset({"", "None", "Escape", "LeftMouseButton"})
# Unreal key names are short words of letters, digits and underscores (Gamepad_FaceButton_Bottom).
NAME = re.compile(r"[A-Za-z0-9_]{1,64}")

option = HiddenOption("open_key", DEFAULT)


def _pressed() -> None:
    from . import control_window
    report.note("open_key_pressed", key=bind.key)
    control_window.start()


bind = keybind("open_window", DEFAULT, _pressed, display_name="Open It Follows",
               description="The key that opens It Follows' window in game.", is_hidden=True)


def key() -> str:
    """The chosen key's Unreal name, the default for a value the file holds that is no key."""
    value = option.value
    return value if valid(value) else DEFAULT


def valid(name: object) -> bool:
    return type(name) is str and NAME.fullmatch(name) is not None and name not in REFUSED


def align() -> bool:
    """The SDK's keybind given the option's key, when they differ; whether it was."""
    if bind.key == key():
        return False
    bind.key = key()
    report.note("open_key_bound", key=bind.key)
    return True


def closer() -> EscapeWatch | None:
    """The watch that closes the window with the key that opens it, deaf until the key is first up: opened by its
    press, the window must not close at its release. None when Windows has no fixed key for it."""
    code = control_console_keys.KEY_NAMES.get(key())
    if code is None:
        return None
    watch = EscapeWatch(key=code)
    watch.muted = True
    return watch
