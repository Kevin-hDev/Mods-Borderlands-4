"""The two keys that put the weapon away, one on the keyboard and one on the controller, each held or pressed as the
player chose. Each is changed in the mod's window, or in the SDK's mod menu. They listen only while the holster runs
(parts.py): its switch off, a key does nothing and nothing held is counted.

A key is never blocked: the game keeps it. Square still reloads on a tap, and a key the player also gave to the game
does both.
"""

import time
from typing import Any

from mods_base import get_pc, keybind

from . import holster_settings, keyboard_place, report
from .controller_option import ControllerKeybindOption
from .holster import Holster
from .key_press import KeyWatch
from .keyboard_option import WheelFreeKeyOption
from .holster_settings import CONTROLLER, KEYBOARD

# Square on a PlayStation controller, X on an Xbox one (Kevin, 2026-09-25: "maintient carré pour ranger l'arme").
CONTROLLER_DEFAULT = "Gamepad_FaceButton_Left"

# Read through this name at each use, so the tests can set the time.
clock = time.perf_counter
_holster = Holster(lambda: clock())
_watches = {KEYBOARD: KeyWatch(), CONTROLLER: KeyWatch()}
_running = False
# Whether the keys in use were written since the keys started listening.
_told = False


def _on(device: str) -> Any:
    def callback(event: Any) -> None:
        if not _running:
            return None
        try:
            name = getattr(event, "name", str(event))
            if _watches[device].event(name, clock(), holster_settings.mode(device)):
                _put_away(device)
        except Exception as exc:
            # A key that fails only leaves the weapon in hand; it must never stop the game from reading the key.
            report.error_once(f"{device}:event", f"{device} key not followed after an error: {exc!r}")
        return None

    return callback


# Hidden binds, each shown once through its option: a visible bind is listed a second time under "Keybinds", and a key
# changed there never reaches the option (Kevin, 2026-09-25, for the other mods: "retire le second").
# Why "Keyboard: Put Away", 2026-09-30: the SDK's text menu now lists the inspection's keys too, "Keyboard: Inspect";
# each entry names its device and its command, or two of the four would read alike (docs/mokup/menu_mods/decisions.md,
# 2026-09-26). The identifiers stay: the players' settings files keep their keys under them.
keyboard_bind = keybind(
    "put_away_keyboard", keyboard_place.default_key(), _on(KEYBOARD),
    display_name="Keyboard: Put Away", description="The keyboard or mouse key that puts your weapon away.",
    is_hidden=True, event_filter=None,
)
controller_bind = keybind(
    "put_away_controller", CONTROLLER_DEFAULT, _on(CONTROLLER),
    display_name="Controller: Put Away", description="The controller button that puts your weapon away.",
    is_hidden=True, event_filter=None,
)
keyboard_key = WheelFreeKeyOption.sole_entry(keyboard_bind)
controller_key = ControllerKeybindOption.sole_entry(controller_bind)
BINDS = {KEYBOARD: keyboard_bind, CONTROLLER: controller_bind}


def pending() -> bool:
    """A key is held toward the hold time: the frames must count it."""
    return any(watch.pending() for watch in _watches.values())


def tick(now: float) -> None:
    for device, watch in _watches.items():
        if watch.tick(now, holster_settings.mode(device), holster_settings.hold_seconds()):
            _put_away(device)


def _put_away(device: str) -> None:
    done = _holster.put_away(get_pc(possibly_loading=True))
    report.note(f"{done} ({device} key {BINDS[device].key}, {holster_settings.mode(device).lower()})")


def going_down(weapon: Any) -> bool:
    """This weapon, still in hand, was put away by a key a moment ago."""
    return _holster.going_down(weapon)


def align() -> None:
    """Gives each bind its option's key. mods_base loads the settings file's own copy of the keys after the options, as
    it is: edited by hand, a key the window refuses, or another than the one shown, would put the weapon away."""
    keyboard_bind.key = keyboard_key.value
    controller_bind.key = controller_key.value


def start() -> None:
    """The keys listen, each on its option's key, with nothing held counted from before."""
    global _running, _told
    align()
    forget()
    _running, _told = True, False


def tell() -> None:
    """Writes the keys and settings in use once after each start, at a frame: the window's Restore and Undo start the
    holster with its switch, before they set the keys and their settings, which come after it (audit of 2026-09-26:
    written at once, the line named the keys from before)."""
    global _told
    if _running and not _told:
        _told = True
        report.note(f"on: {describe()}")


def stop() -> None:
    global _running
    forget()
    _running = False


def running() -> bool:
    return _running


def forget() -> None:
    """A disabled bind never hears the release: a key held then would count on once the mod is back."""
    for watch in _watches.values():
        watch.forget()


def describe() -> str:
    """The keys and settings really in use, for the log: the player's settings file wins over the defaults."""
    parts = [f"{device} {BINDS[device].key or 'no key'} ({holster_settings.mode(device).lower()})" for device in BINDS]
    return f"{', '.join(parts)}, hold {holster_settings.hold_seconds():.2f} s"
