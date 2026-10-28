"""The framing by action and the camera motion options, shared by the three camera mods.

Kevin, 2026-10-06: a switch and one strength per effect, in percent; 100 % is what he found right in the trials, so
a player who wants it softer or stronger moves one slider instead of a setting per action.
"""

from mods_base import BoolOption, SliderOption

from .option_texts import ACTION_FRAMING, ACTION_FRAMING_STRENGTH, CAMERA_MOTION, CAMERA_MOTION_STRENGTH
from .speed_fov_options import bounded

DEFAULT_STRENGTH, MIN_STRENGTH, MAX_STRENGTH = 100, 25, 200


def _strength(identifier: str, texts: dict) -> SliderOption:
    return SliderOption(identifier, DEFAULT_STRENGTH, MIN_STRENGTH, MAX_STRENGTH, step=5, is_integer=True, **texts)


class DynamicOptions:
    def __init__(self):
        self.framing = BoolOption("action_framing", True, **ACTION_FRAMING)
        self.framing_strength = _strength("action_framing_strength", ACTION_FRAMING_STRENGTH)
        self.motion = BoolOption("camera_motion", True, **CAMERA_MOTION)
        self.motion_strength = _strength("camera_motion_strength", CAMERA_MOTION_STRENGTH)
        self.options = [self.framing, self.framing_strength, self.motion, self.motion_strength]

    def values(self) -> tuple[float, float]:
        """The framing's and the motion's share of the trial values: 0 when switched off; a hand-edited file falls
        back to the defaults."""
        return tuple((bounded(strength.value, MIN_STRENGTH, MAX_STRENGTH, DEFAULT_STRENGTH) / 100.0
                      if switch.value is True else 0.0)
                     for switch, strength in ((self.framing, self.framing_strength),
                                              (self.motion, self.motion_strength)))
