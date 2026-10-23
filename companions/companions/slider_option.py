"""A slider's persisted option: whatever the settings file holds, the load goes on and leaves a number within the
slider's bounds (review of 23 October 2026).

mods_base takes a file edited by hand as it is: a value that is no number (null, a list, an object) or an endless one
raises out of the settings' load and leaves the whole mod unloaded, and true reads as 1 (run on the game's own
options.py). Here the load never raises, a value that is no number gives the slider's starting one, one out of its
range its nearest end, one between two steps the nearest step, as the slider shows and the team applies it (a refill
of 3 s would read « 3 s » and be applied as 5 s), and what it had to replace is said once in the SDK log. The recipe
is Benefix Ohm Attack's
slider_option.py, written again here: each mod keeps its own code.
"""

import math
from typing import Any

from mods_base import SliderOption

from . import report

# How much of a value that cannot be read the log shows.
MAX_SHOWN = 40
# The decimals a value brought onto a step keeps.
DIGITS = 6


class BoundedSliderOption(SliderOption):
    def _from_json(self, value: Any) -> None:
        try:
            # A bool is no number here: true would read as 1.
            if type(value) not in (int, float):
                raise TypeError(type(value).__name__)
            super()._from_json(value)
            number = float(self.value)
            if not math.isfinite(number):
                raise OverflowError("endless")
        except (TypeError, OverflowError, ValueError):
            self.value = self.default_value
            report.error_once(f"setting:{self.identifier}", f"the saved value of {self.identifier} "
                              f"({repr(value)[:MAX_SHOWN]}) is no number: it goes on with {self.value}")
            return
        kept = min(max(number, self.min_value), self.max_value)
        kept = min(self.min_value + round((kept - self.min_value) / self.step) * self.step, self.max_value)
        # A decimal step leaves float noise (0.30000000000000004): rounded off, and a value already right left alone.
        kept = round(kept, DIGITS)
        if not math.isclose(kept, number, abs_tol=10 ** -DIGITS):
            self.value = round(kept) if self.is_integer else kept
            report.error_once(f"setting:{self.identifier}", f"the saved value of {self.identifier} "
                              f"({repr(value)[:MAX_SHOWN]}) is off its range or steps: it goes on with {self.value}")
