"""Free Look's options, shared by the three camera mods: on or off, hold or press for each device, and the hold time.

Shown on the CAMERA page after the shoulder transition (Kevin, 2026-10-07: in the camera mods, COMMANDS holds keys
only).
Held by default on both devices: Kevin's Free Look lasts while the key is held. 0.20 s is his hold time
(2026-10-06), short enough to feel at once, long enough to leave a tap of L3 to the game's sprint.
On by default; switched off, its keys do nothing (Kevin, 2026-10-08: « il faut pouvoir le désactiver avec un toggle »).
"""

from typing import NamedTuple

from mods_base import BoolOption, SliderOption

from .option_texts import FREE_LOOK, FREE_LOOK_CONTROLLER_HOLD, FREE_LOOK_HOLD_TIME, FREE_LOOK_KEYBOARD_HOLD
from .speed_fov_options import bounded

KEYBOARD_ID, CONTROLLER_ID = "free_look_key", "free_look_controller"
DEFAULT_HOLD_S, MIN_HOLD_S, MAX_HOLD_S = 0.20, 0.10, 1.00


class Values(NamedTuple):
    keys: tuple
    holds: tuple
    hold_s: float


class FreeLookOptions:
    def __init__(self, commands) -> None:
        self.commands = commands
        self.switch = BoolOption("free_look", True, **FREE_LOOK)
        self.keyboard_hold = BoolOption("free_look_keyboard_hold", True, **FREE_LOOK_KEYBOARD_HOLD)
        self.controller_hold = BoolOption("free_look_controller_hold", True, **FREE_LOOK_CONTROLLER_HOLD)
        self.hold_time = SliderOption("free_look_hold_time", DEFAULT_HOLD_S, MIN_HOLD_S, MAX_HOLD_S, step=0.05,
                                      is_integer=False, **FREE_LOOK_HOLD_TIME)
        self.options = [self.switch, self.keyboard_hold, self.controller_hold, self.hold_time]

    def values(self) -> Values | None:
        """None while switched off; a hand-edited file falls back to the defaults."""
        if self.switch.value is False:
            return None
        keys = tuple(self.commands.option(identifier).value for identifier in (KEYBOARD_ID, CONTROLLER_ID))
        holds = tuple(option.value is not False for option in (self.keyboard_hold, self.controller_hold))
        return Values(keys, holds, bounded(self.hold_time.value, MIN_HOLD_S, MAX_HOLD_S, DEFAULT_HOLD_S))
