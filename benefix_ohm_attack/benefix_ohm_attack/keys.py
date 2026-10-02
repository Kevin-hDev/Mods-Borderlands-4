"""The beam's two keys, one on the keyboard or mouse and one on the controller: held to fire. None is bound until
the player chooses his on the window's COMMANDS page (Kevin, 2026-10-01: no key by default).

A key is never blocked: the game keeps it. Each key's option is its one authority (key_option.py, the camera
runtime's): the window saves the option, and `align` gives the bind its option's key.
"""

from typing import Any, Callable

from mods_base import keybind

from .key_option import ControllerKeybindOption
from .keyboard_option import WheelFreeKeyOption

KEYBOARD, CONTROLLER = "keyboard", "controller"
# A mouse button pressed twice quickly comes as a double click, not as a second press: both hold the key down.
DOWN, UP = ("IE_Pressed", "IE_DoubleClick"), "IE_Released"

# The devices whose key is down.
_down: set[str] = set()


def held() -> bool:
    return bool(_down)


def release() -> None:
    """Forgets a key still down: a menu, a loading or a switched-off mod never sees its release."""
    _down.clear()


def _on(device: str) -> Callable[[Any], None]:
    def callback(event: Any) -> None:
        name = str(getattr(event, "name", event))
        if name.endswith(DOWN):
            _down.add(device)
        elif name.endswith(UP):
            _down.discard(device)

    return callback


# Hidden binds, each shown once through its option: a visible bind is listed a second time under "Keybinds" in the
# SDK's menu, and a key changed there never reaches the option. Each entry names its device, or the two would read
# alike (docs/mokup/menu_mods/decisions.md, 2026-09-25 and 26).
keyboard_bind = keybind(
    "fire_keyboard", None, _on(KEYBOARD),
    display_name="Keyboard: Fire Beam", description="The keyboard or mouse key to hold to fire the beam.",
    is_hidden=True, event_filter=None,
)
controller_bind = keybind(
    "fire_controller", None, _on(CONTROLLER),
    display_name="Controller: Fire Beam", description="The controller button to hold to fire the beam.",
    is_hidden=True, event_filter=None,
)
# Not the wheel (keyboard_option.py): its notch is a press and a release in the same frame, never a hold.
keyboard_key = WheelFreeKeyOption.sole_entry(keyboard_bind)
controller_key = ControllerKeybindOption.sole_entry(controller_bind)


def align() -> None:
    """Gives each bind its option's key, with nothing held counted from before. mods_base loads the settings file's
    own copy of the keys after the options, as it is: edited by hand, another key than the one shown would fire."""
    keyboard_bind.key = keyboard_key.value
    controller_bind.key = controller_key.value
    release()
