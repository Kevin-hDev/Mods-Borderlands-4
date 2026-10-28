# Generated: the settings window Kevin's mods share, taken from Apex Heirloom's and put under this mod's names.
# Its comments may speak of that mod. Never edited by hand: the window's generator writes this file.
"""A slider's value as the mod may use it, whatever the settings file holds.

mods_base loads a settings file edited by hand as it is (audit of Tidy Weapons, 2026-09-25): out of the slider's range
the nearest bound holds, and what is not a number gives the default. The heirloom and the holster read their sliders
through this, since they became one mod (2026-09-26).
"""

import math
from typing import Any


def bounded(option: Any) -> float:
    try:
        value = float(option.value)
    except (TypeError, ValueError):
        return float(option.default_value)
    if math.isnan(value):
        return float(option.default_value)
    return min(max(value, option.min_value), option.max_value)
