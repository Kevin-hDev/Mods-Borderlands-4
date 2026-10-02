# Generated: the settings window Kevin's mods share, taken from Apex Heirloom's and put under this mod's names.
# Its comments may speak of that mod. Never edited by hand: the window's generator writes this file.
"""The rules on the COMMANDS page's keys, which the page's actions (command_actions.py, Apex Movement's) call as
Movement's call the camera runtime's commands: which option a card's row sets, the keys by default, and the checks a
key passes before it is saved.

Why each refusal has its own words (panel_en.py, panel_fr.py), the previous key always kept: a player told the real
cause knows what to choose instead. A key is refused when:
- another command holds it on the same device, as the camera commands refuse theirs
  (docs/mokup/menu_mods/decisions.md, 2026-09-26): one press would put the weapon away and inspect the heirloom;
- it is the mouse wheel, on the keyboard's row (keyboard_option.py): the game changes weapon with it;
- it is a console key, or Escape, which cancels a capture (control_reserved.py), as Grapple's page refused them;
- it is a controller button on the keyboard's row, or a key on the controller's.

Only the window refuses a key another command holds: mods_base loads the saved keys one by one, and a check there would
drop a key that met another's default before that one was loaded.
"""

from typing import Any

from . import control_config, control_reserved, report
from .controller_option import normalize_key
from .control_config import CONTROLLER, KEYBOARD
from .keyboard_option import WHEEL

# Grapple's reserved keys: Escape cancels a capture, Tilde opens the console.
RESERVED_KEYS = frozenset(("Escape", "Tilde"))


class Refused(ValueError):
    """A key refused, `status` naming the window's words for why."""

    def __init__(self, status: str) -> None:
        super().__init__(status)
        self.status = status


class CommandKeys:
    def __init__(self, commands: tuple) -> None:
        self.commands = commands
        self._slots = {(command.name, device): option for command in commands
                       for device, option in ((KEYBOARD, command.keyboard), (CONTROLLER, command.controller))}
        self.options = tuple(self._slots.values())
        self._places = {option.identifier: place for place, option in self._slots.items()}

    def identifier(self, action: str, device: str) -> str:
        option = self._slots.get((action, device))
        if option is None:
            raise ValueError("invalid command")
        return option.identifier

    def defaults(self) -> dict[str, str | None]:
        """The keys RESET CONTROLS puts back: the put-away keys' own, none for the inspection (Kevin, 2026-09-30).
        A greyed card's too: the button promises every key back, and they wait for their part to be switched on."""
        return {option.identifier: option.default_value for option in self.options}

    def validate(self, changes: Any) -> dict[str, str | None]:
        if type(changes) is not dict or not 0 < len(changes) <= len(self.options):
            raise ValueError("invalid command changes")
        if any(type(identifier) is not str or identifier not in self._places for identifier in changes):
            raise ValueError("unknown command")
        normalized = {identifier: self._normalized(identifier, value) for identifier, value in changes.items()}
        final = {option.identifier: normalized.get(option.identifier, option.value) for option in self.options}
        for identifier, value in normalized.items():
            if value is None:
                continue
            device = self._places[identifier][1]
            for other, (other_action, other_device) in self._places.items():
                if other != identifier and other_device == device and final[other] == value:
                    raise Refused(f"duplicate_{other_action}")
        return normalized

    def _normalized(self, identifier: str, value: Any) -> str | None:
        device = self._places[identifier][1]
        if device == KEYBOARD and type(value) is str and value in WHEEL:
            raise Refused("wheel_key")
        try:
            return normalize_key(self._slots[self._places[identifier]], value)
        except ValueError:
            raise Refused(f"invalid_{device}") from None

    def set_values(self, changes: Any) -> dict[str, str | None]:
        normalized = self.validate(changes)
        for identifier, value in normalized.items():
            self._slots[self._places[identifier]].value = value
        return normalized

    def align(self) -> None:
        """Gives each bind its option's key, as the parts do when they start (keys.align, inspect_keys.start)."""
        for command in self.commands:
            for bind, option in zip(command.binds, (command.keyboard, command.controller)):
                bind.key = option.value

    @staticmethod
    def refusal(key: Any) -> str | None:
        """Why a key the player just captured is refused before any other check, or None: the console's keys."""
        if key is None:
            return None
        if key in RESERVED_KEYS:
            return "reserved_key"
        try:
            reserved = control_reserved.console_keys()
        except Exception:
            # A key whose conflict with the console could not be checked is not saved.
            report.error_once("controls:console_keys", "console shortcuts unavailable; controls kept")
            return "failed"
        return "reserved_key" if key in reserved else None


KEYS = CommandKeys(control_config.COMMANDS)
