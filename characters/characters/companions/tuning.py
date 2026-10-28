"""What a companion is given at each of its births by the mod that runs the team (decision 69 of docs/renforts): its
health, a multiple of the hunter's most health; its shield, a share of that health, 0 for none; the wait before a
broken shield fills again, None for never; its speed bonus; the wait before it comes back from a death; for a hunter,
his own outfit or the player's colours; and what chose these values, for the journal. Each mod has its own way:
levels and cards in one, five settings for the whole team in the other (spec-compagnons.md, « Le mod dédié »).

Checked here, the one frontier: a value out of its bounds is brought back inside, a value that is no number takes the
starting one, so that a settings file edited by hand never writes a health of nothing, a shield past the health, a
speed that deforms the walk (decision 6) nor a wait of no time. The bounds hold the five settings' ranges of decision
67, the widest any mod offers.
"""

import math
from typing import Any, NamedTuple

TIMES = (1.0, 20.0)
SHIELD = (0.0, 1.0)
REFILL_AFTER_S = (5.0, 120.0)
SPEED = (1.0, 1.5)
BACK_AFTER_S = (10.0, 120.0)
OUTFITS = ("own", "player")
MAX_TEXT = 40


class Tuning(NamedTuple):
    times: float
    shield: float
    refill_after_s: float | None
    speed: float
    back_after_s: float
    outfit: str
    # (what chose the values, why): a level and why it was played, or the settings.
    said: tuple[str, str]


# The starting values of decision 67: those the team gets outside It Follows' modes (Bandit, decision 38), and the
# ones a companion gets when its mod's values could not be read.
STARTING = Tuning(4.0, 0.3, None, 1.2, 45.0, "own", ("starting", "unread"))


def _number(value: Any) -> bool:
    # A bool is no number here: True would read as a health of 1.
    return type(value) in (int, float) and math.isfinite(value)


def _within(value: Any, bounds: tuple[float, float], starting: Any) -> Any:
    return min(max(float(value), bounds[0]), bounds[1]) if _number(value) else starting


def _text(value: Any) -> str:
    return value[:MAX_TEXT] if isinstance(value, str) else ""


def checked(given: Any) -> Tuning:
    """The values given, each brought within its bounds; the starting ones for anything that is no Tuning."""
    if not isinstance(given, Tuning):
        return STARTING
    said = given.said if isinstance(given.said, tuple) and len(given.said) == 2 else STARTING.said
    return Tuning(times=_within(given.times, TIMES, STARTING.times),
                  shield=_within(given.shield, SHIELD, STARTING.shield),
                  refill_after_s=_within(given.refill_after_s, REFILL_AFTER_S, STARTING.refill_after_s),
                  speed=_within(given.speed, SPEED, STARTING.speed),
                  back_after_s=_within(given.back_after_s, BACK_AFTER_S, STARTING.back_after_s),
                  outfit=given.outfit if given.outfit in OUTFITS else STARTING.outfit,
                  said=(_text(said[0]), _text(said[1])))


def written(one: Tuning) -> list:
    """The values as the journal writes them: times, shield, refill wait, speed, back wait, outfit, what chose them
    and why."""
    return [one.times, one.shield, one.refill_after_s, one.speed, one.back_after_s, one.outfit, *one.said]
