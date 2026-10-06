"""The command the CAMERA page's key card sets (Kevin, 2026-10-06): the view key, one keyboard/mouse key and one
controller button. Each key's option stays its one authority (view_key.py); the page reads and saves the options named
here, as Apex Heirloom's COMMANDS page reads its control_config.py.
"""

from typing import Any, NamedTuple

from . import view_key

KEYBOARD, CONTROLLER = "keyboard", "controller"


class Command(NamedTuple):
    name: str  # its card's words are command_<name> and command_<name>_desc in panel_en.py and panel_fr.py
    keyboard: Any  # the keyboard or mouse key's option
    controller: Any  # the controller button's option
    binds: tuple  # the keyboard's bind then the controller's, which the options' keys reach


COMMANDS = (Command("view", view_key.keyboard_key, view_key.controller_key,
                    (view_key.keyboard_bind, view_key.controller_bind)),)
SLOTS = tuple((command.name, device) for command in COMMANDS for device in (KEYBOARD, CONTROLLER))
