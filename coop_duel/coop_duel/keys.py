"""Co-op Duel's two keys (Kevin, 17 October 2026): F9 opens the window, N starts the duel or stops it. Each can be
changed on the OPTIONS page (panel_keys.py). Each key's one authority is a hidden option of the settings file, written
through the window's settings transaction; its SDK keybind is given the key from it (align), at start and whenever the
window polls. Taken from It Follows' open_key.py, its key seen working in game: one class serves both keys here.

The duel's key does nothing while the window is open: the key's field may be waiting for that very key, and the window
has its own buttons. A start it refuses says why on the screen (banner.py), as the window's footer would."""

import re
from typing import Callable

from mods_base import HiddenOption, keybind

from . import control_console_keys, report
from .control_escape import EscapeWatch

# Never a shortcut: Escape closes the window and cancels a choice; the left button is a click on the menu, which the
# key's field reports when it is clicked a second time.
REFUSED = frozenset({"", "None", "Escape", "LeftMouseButton"})
# Unreal key names are short words of letters, digits and underscores (Gamepad_FaceButton_Bottom).
NAME = re.compile(r"[A-Za-z0-9_]{1,64}")


class Shortcut:
    def __init__(self, identifier: str, default: str, pressed: Callable[[], None], display_name: str,
                 description: str) -> None:
        self.identifier, self.default = identifier, default
        self.option = HiddenOption(identifier, default)

        def press() -> None:
            report.note("key pressed", key=identifier, name=self.bind.key)
            pressed()

        self.bind = keybind(identifier, default, press, display_name=display_name, description=description,
                            is_hidden=True)

    def key(self) -> str:
        """The chosen key's Unreal name, the default for a value the file holds that is no key."""
        value = self.option.value
        return value if valid(value) else self.default

    def align(self) -> bool:
        """The SDK's keybind given the option's key, when they differ; whether it was."""
        if self.bind.key == self.key():
            return False
        self.bind.key = self.key()
        report.note("key bound", key=self.identifier, name=self.bind.key)
        return True


def valid(name: object) -> bool:
    return type(name) is str and NAME.fullmatch(name) is not None and name not in REFUSED


def _open() -> None:
    from . import control_window
    control_window.start()


def _duel() -> None:
    from . import control_window, duel, panel_preferences
    if control_window.active():
        report.note("duel key ignored", why="window_open")
        return
    language = panel_preferences.language.value
    if duel.live() is not None:
        duel.stop("stopped")
        return
    outcome = duel.start(language)
    if outcome != "started":
        duel.refused(outcome, language)


OPEN = Shortcut("open_key", "F9", _open, "Open Co-op Duel", "The key that opens Co-op Duel's window in game.")
DUEL = Shortcut("duel_key", "N", _duel, "Start or stop the duel", "The key that starts the duel, or stops it.")
ALL = (OPEN, DUEL)


def align() -> bool:
    return any([shortcut.align() for shortcut in ALL])


def taken_by_other(shortcut: Shortcut, name: str) -> bool:
    """Whether another of the mod's keys already uses name: one key would then do two things."""
    return any(other is not shortcut and other.key() == name for other in ALL)


def closer() -> EscapeWatch | None:
    """The watch that closes the window with the key that opens it, deaf until the key is first up: opened by its
    press, the window must not close at its release. None when Windows has no fixed key for it."""
    code = control_console_keys.KEY_NAMES.get(OPEN.key())
    if code is None:
        return None
    watch = EscapeWatch(key=code)
    watch.muted = True
    return watch
