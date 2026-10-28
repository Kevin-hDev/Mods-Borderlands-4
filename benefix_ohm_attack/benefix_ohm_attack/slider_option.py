"""A slider's persisted option: whatever the settings file holds, the load goes on and leaves a number within the
slider's bounds.

mods_base takes a file edited by hand as it is. A value that is no number (null, a list) or an endless one raises
out of the settings' load, which leaves the whole mod unloaded; a number out of the slider's range is kept (audit
of 2026-10-01, run on the game's own options.py). Here the load never raises, and what it had to replace is said.

The file is not the only way in: the SDK's console menu writes whatever number the player types. So the attack
still reads each slider through slider_values.bounded, as the window does (review of 2026-10-02).

With the SDK's own class a change callback set on the option is called at each assignment of the load, the first
with the value as the file gives it: none is set on this mod's sliders.
"""

from typing import Any

from mods_base import SliderOption

from . import report
from .slider_values import bounded

# How much of a value that cannot be read the log shows.
MAX_SHOWN = 40


class BoundedSliderOption(SliderOption):
    def _from_json(self, value: Any) -> None:
        unread = False
        try:
            super()._from_json(value)
        except (TypeError, OverflowError):
            unread = True
        loaded = self.value
        kept = bounded(self)
        self.value = round(kept) if self.is_integer else kept
        # Not-a-number equals nothing, itself included: it is said as replaced too.
        if unread or self.value != loaded:
            report.error_once(f"setting:{self.identifier}", f"the saved value of {self.identifier} "
                              f"({repr(value)[:MAX_SHOWN]}) is not one the mod can use: it goes on with {self.value}")
