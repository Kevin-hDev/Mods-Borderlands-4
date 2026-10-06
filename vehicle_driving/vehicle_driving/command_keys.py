"""The rules on the CAMERA page's keys, which the page's actions (command_actions.py, Apex Movement's) call: which
option a row sets, the keys by default, and the checks a key passes before it is saved.

Apex Heirloom's command_keys.py, without its two rules that cannot apply here: a key another command holds (this page
has one command, and its two rows are on different devices) and the mouse wheel (Heirloom's keys put a weapon away,
which the wheel changes). Why each refusal has its own words (panel_en.py, panel_fr.py), the previous key always kept:
a player told the real cause knows what to choose instead. A key is refused when:
- it is a console key, or Escape, which cancels a capture (control_reserved.py);
- it is a controller button on the keyboard's row, or a key on the controller's, or the left mouse button, which
  fires the weapon (key_option.py).
"""

from typing import Any

from . import control_config, control_reserved, report
from .control_config import CONTROLLER, KEYBOARD
from .key_option import normalize_controller_key, normalize_keyboard_key

# Escape cancels a capture, Tilde opens the console.
RESERVED_KEYS = frozenset(("Escape", "Tilde"))
_NORMALIZE = {KEYBOARD: normalize_keyboard_key, CONTROLLER: normalize_controller_key}


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
        """The keys the page's reset puts back: L and no controller button."""
        return {option.identifier: option.default_value for option in self.options}

    def validate(self, changes: Any) -> dict[str, str | None]:
        if type(changes) is not dict or not 0 < len(changes) <= len(self.options):
            raise ValueError("invalid command changes")
        if any(type(identifier) is not str or identifier not in self._places for identifier in changes):
            raise ValueError("unknown command")
        return {identifier: self._normalized(identifier, value) for identifier, value in changes.items()}

    def _normalized(self, identifier: str, value: Any) -> str | None:
        device = self._places[identifier][1]
        try:
            return _NORMALIZE[device](value)
        except ValueError:
            raise Refused(f"invalid_{device}") from None

    def set_values(self, changes: Any) -> dict[str, str | None]:
        normalized = self.validate(changes)
        for identifier, value in normalized.items():
            self._slots[self._places[identifier]].value = value
        return normalized

    def align(self) -> None:
        """Gives each bind its option's key: mods_base loads the file's keybinds after its options, and a key edited
        there alone would otherwise outlive the option, the one authority."""
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
            # A key whose clash with the console could not be checked is not saved.
            report.error_once("controls:console_keys", "console shortcuts unavailable; controls kept")
            return "failed"
        return "reserved_key" if key in reserved else None


KEYS = CommandKeys(control_config.COMMANDS)
