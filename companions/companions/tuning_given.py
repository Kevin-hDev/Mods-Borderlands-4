"""What each companion is given in Companions (characters/companions/tuning.py): the SETTINGS page's five values, the
same for every companion (decision 68 of docs/renforts), and the outfit chosen on the card of the hunter the player
plays. Read once, when the team starts (session.start_team): the team runs with the settings it started with, as its
cards are locked while it is on. The sliders read the settings file tolerantly (slider_option.py); a value that is
still no number here, set by other means, reads as the slider's starting one, and each value is brought within its
bounds by the characters' package (tuning.checked).
"""

import math
from typing import Any, Callable

from . import settings, team_choices
from .characters.companions import tuning

PERCENT = 100.0
# What chose the values, as the journal writes it (tuning.written).
SAID = ("settings", "companions")


def _number(option: Any) -> float:
    value = option.value
    # A bool is no number here: True would give a health of 1.
    if type(value) in (int, float) and math.isfinite(value):
        return float(value)
    return float(option.default_value)


def given() -> Callable[[str], tuning.Tuning]:
    """The team's settings and the outfits read now; for each companion, by its name, what it is given."""
    refill = _number(settings.refill)
    shared = (_number(settings.health), _number(settings.shield) / PERCENT,
              None if refill <= settings.NEVER else refill, 1.0 + _number(settings.speed) / PERCENT,
              _number(settings.back))
    outfits = dict(settings.outfits.value) if isinstance(settings.outfits.value, dict) else {}
    return lambda name: tuning.Tuning(*shared, team_choices.outfit(name, outfits), SAID)
