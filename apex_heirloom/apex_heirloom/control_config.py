"""The commands the COMMANDS page sets, one card each with a keyboard/mouse key and a controller button: the keys that
put the weapon away (keys.py), then those that inspect the heirloom (inspect_keys.py). Each key's option stays its one
authority; the page reads and saves the options named here, as Apex Movement's reads its camera_control_config.py.

Why, Kevin, 2026-09-30 (docs/mokup/menu_mods/decisions.md, sketch I1): « Ranger l'arme » then « Inspecter », every key
of the mod in one place, chosen the way every menu of ours chooses one. A separate file sets its own part's command
only (pack.py): Tidy Weapons the put-away keys, Heirloom the inspection's.
"""

from typing import Any, NamedTuple

from . import heirloom_settings, holster_settings, inspect_keys, keys, pack
from .holster_settings import CONTROLLER, KEYBOARD


class Command(NamedTuple):
    name: str  # its card's words are command_<name> in panel_en.py and panel_fr.py
    part: str  # the switch of the part it serves, which greys its card (menu.COMMANDS_DEPEND_ON)
    keyboard: Any  # the keyboard or mouse key's option
    controller: Any  # the controller button's option
    binds: tuple  # the keyboard's bind then the controller's, which the options' keys reach


_ALL = (
    Command("put_away", holster_settings.holster.identifier, keys.keyboard_key, keys.controller_key,
            (keys.keyboard_bind, keys.controller_bind)),
    Command("inspect", heirloom_settings.heirloom.identifier, inspect_keys.keyboard_key, inspect_keys.controller_key,
            (inspect_keys.keyboard_bind, inspect_keys.controller_bind)),
)
COMMANDS = tuple(command for command in _ALL if pack.runs(command.part))
SLOTS = tuple((command.name, device) for command in COMMANDS for device in (KEYBOARD, CONTROLLER))
# The keys the window's Restore and Undo save with the settings (panel_model.py): put back, the put-away keys take
# their defaults and the inspection's none (Kevin, 2026-09-30: « aucune par défaut »).
ALL = tuple(option for command in COMMANDS for option in (command.keyboard, command.controller))
