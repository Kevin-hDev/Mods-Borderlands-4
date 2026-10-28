"""The shoulder options shared by the camera mods: the automatic switch first (shoulder_auto_options.py), then the
timing that shoulder and camera-mode switches share, never native-climb timing.
"""
import math
from mods_base import BoolOption, SliderOption
from . import option_texts, transition_catalog as timing
from .shoulder_auto_options import ShoulderAutoOptions

class ShoulderTransitionOptions:
    def __init__(self):
        # Right after the shoulder on the CAMERA page (Kevin, 2026-10-07).
        self.automatic = ShoulderAutoOptions()
        self.smooth = BoolOption('shoulder_smooth', True, **option_texts.SHOULDER_SMOOTH)
        # Keep the saved Orbit ID: it now controls FP/TP and Orbit together.
        self.orbit_smooth = BoolOption('orbit_smooth', True, **option_texts.ORBIT_SMOOTH)
        self.duration = SliderOption(
            'shoulder_seconds', timing.SHOULDER_SECONDS_DEFAULT,
            timing.SHOULDER_SECONDS_MIN, timing.SHOULDER_SECONDS_MAX,
            step=timing.SHOULDER_SECONDS_STEP, is_integer=False, **option_texts.SHOULDER_SECONDS)
        self.options = (*self.automatic.options, self.smooth, self.orbit_smooth, self.duration)

    def seconds(self):
        if self.smooth.value is not True:
            return 0.0
        return self._duration()

    def orbit_seconds(self):
        return self._duration() if self.orbit_smooth.value is True else 0.0

    def _duration(self):
        value = self.duration.value
        if type(value) not in (int, float) or not math.isfinite(value):
            value = timing.SHOULDER_SECONDS_DEFAULT
        return float(min(timing.SHOULDER_SECONDS_MAX, max(timing.SHOULDER_SECONDS_MIN, value)))
