"""The speed FOV's options, shared by the three camera mods; each elected mod saves its own player choice."""
import math
from mods_base import BoolOption, SliderOption

from .option_texts import SPEED_FOV, SPEED_FOV_GAIN, SPEED_FOV_SECONDS

# Kevin, 2026-10-06: Apex adds 10; in game +10 felt a little too strong; after trying 7 and 8 he kept 7.
DEFAULT_GAIN, MIN_GAIN, MAX_GAIN = 7, 1, 30
DEFAULT_SECONDS, MIN_SECONDS, MAX_SECONDS = 0.4, 0.1, 2.0


class SpeedFovOptions:
    def __init__(self):
        self.enabled = BoolOption("speed_fov", True, **SPEED_FOV)
        self.gain = SliderOption("speed_fov_gain", DEFAULT_GAIN, MIN_GAIN, MAX_GAIN, step=1, is_integer=True,
                                 **SPEED_FOV_GAIN)
        self.seconds = SliderOption("speed_fov_seconds", DEFAULT_SECONDS, MIN_SECONDS, MAX_SECONDS, step=0.1,
                                    is_integer=False, **SPEED_FOV_SECONDS)
        self.options = [self.enabled, self.gain, self.seconds]

    def values(self) -> tuple[bool, float, float]:
        """The switch, the gain and the transition seconds; a hand-edited file falls back to the defaults."""
        return (self.enabled.value is True, bounded(self.gain.value, MIN_GAIN, MAX_GAIN, DEFAULT_GAIN),
                bounded(self.seconds.value, MIN_SECONDS, MAX_SECONDS, DEFAULT_SECONDS))


def bounded(value, low, high, default) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return float(default)
    return float(min(high, max(low, value)))
