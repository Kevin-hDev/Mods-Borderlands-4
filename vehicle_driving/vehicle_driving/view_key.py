"""The view key: at the wheel, each press goes to the next camera view and saves it (spec section 3.8).

A keyboard key and a controller button, each a setting of the mod shown once: on the window's CAMERA page and in the
SDK's mod menu. Their SDK binds are hidden, as Apex Heirloom's: a visible bind is listed a second time under
"Keybinds", and a key changed there never reaches the option (from_keybind copies the option to the bind only).

The key is never blocked: the callback returns None, and mods_base holds a key back only for a returned Block, so the
game and the other mods still get it (spec section 4). It catches every error, which must never reach the game's
input.
"""

from typing import Callable

from mods_base import get_pc, keybind

from . import report, seat, settings
from .key_option import ControllerKeybindOption, KeyboardKeybindOption

# Kevin, 2026-10-06: "on va conserver L par defaut"; the controller has none until he picks one.
KEYBOARD_KEY = "L"


def press(save: Callable[[], None]) -> None:
    """Goes to the next view at the wheel, then saves it; on foot, does nothing."""
    try:
        if seat.driven_vehicle(get_pc(possibly_loading=True)) is None:
            return
        settings.vehicle_view.value = settings.next_view(settings.current_view())
    except Exception as exc:
        report.error_once(f"view key:{type(exc).__name__}", f"the view key failed: {exc!r}")
        return
    try:
        save()
    except Exception as exc:
        # The view stays: the player sees it, and the next save of the settings writes it. A save fails while the
        # settings window is saving, or when the disk refuses the file.
        report.error_once(f"view key save:{type(exc).__name__}", f"the camera view could not be saved: {exc!r}")


def _save_settings() -> None:
    # The mod is built after its binds (__init__.py), and only read once the key is pressed.
    from . import mod
    mod.save_settings()


def _on_press() -> None:
    press(_save_settings)


keyboard_bind = keybind("vehicle_view_key", KEYBOARD_KEY, _on_press, display_name="View key",
                        description="At the wheel, goes to the next camera view.", is_hidden=True)
controller_bind = keybind("vehicle_view_button", None, _on_press, display_name="View button",
                          description="At the wheel, goes to the next camera view, on a controller.", is_hidden=True)
keyboard_key = KeyboardKeybindOption.sole_entry(keyboard_bind)
controller_key = ControllerKeybindOption.sole_entry(controller_bind)
BINDS = [keyboard_bind, controller_bind]
OPTIONS = [keyboard_key, controller_key]
