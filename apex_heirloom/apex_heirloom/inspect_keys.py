"""The two keys that inspect the heirloom, one on the keyboard and one on the controller: a press plays the chosen
heirloom's inspection while it shows in the empty hand (heirloom.inspect). They act only while the heirloom runs
(parts.py, lifecycle.py): its switch off, a key does nothing.

Why a key of its own, 2026-09-29 (cosmetics/heirloom/docs/heirloom.md, section 20): Kevin wants it « réglable dans le
menu ». Where, Kevin, 2026-09-30 (docs/mokup/menu_mods/decisions.md, sketch I1): on the COMMANDS page, the card
« Inspecter » under « Ranger l'arme » (control_config.py). Why none by default, Kevin, the same day: « aucune par défaut
assignable dans le menu pour manette et clavier/souris »: the player chooses each, and no key the game or another mod
already uses is taken for him.

A key is never blocked: the game keeps it. One gesture per press (Kevin, 2026-09-25): a press or a mouse double click
starts it, a key held does not repeat it.
"""

from typing import Any, Callable

from mods_base import keybind
from unrealsdk import logging

from . import heirloom, lifecycle
from .key_option import ControllerKeybindOption
from .keyboard_option import WheelFreeKeyOption
from .key_press import PRESSES

KEYBOARD, CONTROLLER = "keyboard", "controller"

# The devices whose key already failed since the heirloom started: a key pressed again and again must not fill the log.
_failed: set[str] = set()


def _on(device: str) -> Callable[[Any], None]:
    def callback(event: Any) -> None:
        try:
            if lifecycle.STATE.running and getattr(event, "name", str(event)) in PRESSES:
                heirloom.inspect()
        except Exception as exc:
            # A key that fails only leaves the heirloom still; it must never stop the game from reading the key.
            if device not in _failed:
                _failed.add(device)
                logging.error(f"{heirloom.PREFIX} {device} inspection key not followed after an error: {exc!r}")
        return None

    return callback


# Hidden binds, each shown once through its option, as the put-away keys (keys.py). Each entry of the SDK's text menu
# names its device (docs/mokup/menu_mods/decisions.md, 2026-09-26: two entries of one command must not read alike).
keyboard_bind = keybind(
    "inspect_keyboard", None, _on(KEYBOARD),
    display_name="Keyboard: Inspect", description="The keyboard or mouse key that inspects your heirloom.",
    is_hidden=True, event_filter=None,
)
controller_bind = keybind(
    "inspect_controller", None, _on(CONTROLLER),
    display_name="Controller: Inspect", description="The controller button that inspects your heirloom.",
    is_hidden=True, event_filter=None,
)
# Why not the wheel, 2026-09-30, as the put-away key (keyboard_option.py): the game changes weapon with it, which would
# cut the inspection it starts.
keyboard_key = WheelFreeKeyOption.sole_entry(keyboard_bind)
controller_key = ControllerKeybindOption.sole_entry(controller_bind)


def start() -> None:
    """Gives each bind its option's key, as the heirloom starts: mods_base loads the settings file's own copy of the
    keys after the options, as it is (keys.align). A failure is said again after a new start."""
    keyboard_bind.key = keyboard_key.value
    controller_bind.key = controller_key.value
    _failed.clear()
