"""The commands the COMMANDS page sets, one card each with a keyboard/mouse key and a controller button: the beam's
key is the only one. Each key's option stays its one authority (keys.py); the page reads and saves the options named
here, as Apex Heirloom's reads its own control_config.py (sketch C, docs/attaque-rayon/esquisses_menu/C.png).
"""

from typing import Any, NamedTuple

from . import keys
from .keys import CONTROLLER, KEYBOARD  # noqa: F401  the window's key rules take the devices' names from here


class Command(NamedTuple):
    name: str  # its card's words are command_<name> and command_<name>_desc in panel_en.py and panel_fr.py
    keyboard: Any  # the keyboard or mouse key's option
    controller: Any  # the controller button's option
    binds: tuple  # the keyboard's bind then the controller's, which the options' keys reach


COMMANDS = (Command("fire", keys.keyboard_key, keys.controller_key, (keys.keyboard_bind, keys.controller_bind)),)
SLOTS = tuple((command.name, device) for command in COMMANDS for device in (KEYBOARD, CONTROLLER))
# The keys the window's Restore and Undo save with the settings (panel_model.py): put back, none is bound.
ALL = tuple(option for command in COMMANDS for option in (command.keyboard, command.controller))
