"""The speeds every movement reads, kept in the order Kevin set whatever the sliders say (design decision 9).

Split from settings.py on 2026-09-18: that file declares the settings, this one holds the one rule that ties sliders
of different movements together. A slider cannot take another slider as its bound, so the order is enforced here.
"""

from dataclasses import dataclass
from typing import Any

from . import ownership, pack, settings

# The game's own ground speeds, measured with the bare game (2026-09-15). A file that does not carry the speeds orders
# its own against these: the sliders of a separate Apex Speed file live in that file's settings, which this one never
# loads, so reading its own copy of them would compare with a default nobody set (review, 2026-09-18).
GAME_WALK = 540.0
GAME_SPRINT = 828.0
# The character's speed scale, lowered by the ground speed under the walk key and read by the slides: a key both
# movements name, so it lives here rather than in either.
SCALE_KEY = "movement.MaxGroundSpeedScale.Value"


@dataclass(frozen=True)
class Speeds:
    walk: float
    sprint: float
    slide: float
    landing_slide_min: float
    slide_max: float


def ordered(walk: float, sprint: float, slide: float, landing_slide_min: float, slide_max: float) -> Speeds:
    """Keeps walk <= sprint <= slide <= slide top speed and the landing slide minimum <= sprint.

    The top speed joined the order on 2026-09-18: set under the start speed, a slide started fast and dropped to it on
    its first frame, against the promise of its own description.
    """
    sprint = max(sprint, walk)
    slide = max(slide, sprint)
    return Speeds(walk=walk, sprint=sprint, slide=slide, landing_slide_min=min(landing_slide_min, sprint),
                  slide_max=max(slide_max, slide))


def speeds() -> Speeds:
    carries_speeds = pack.carries("Movement")
    return ordered(
        float(settings.walk_speed.value) if carries_speeds else GAME_WALK,
        float(settings.sprint_speed.value) if carries_speeds else GAME_SPRINT,
        float(settings.slide_speed.value), float(settings.landing_slide_min_speed.value),
        float(settings.slide_max_speed.value),
    )


def game_scale(movement: Any) -> float:
    """The character's speed scale as the game has it, even while the walk key's lower one is written in its place."""
    if ownership.is_owned(SCALE_KEY):
        return float(ownership.original(SCALE_KEY))
    return float(movement.MaxGroundSpeedScale.Value)


def walk_key_speed() -> float:
    """The walk key's speed, never above the walk; the game's own walk in a file that does not carry the speeds."""
    # Imported here: walk_key takes GAME_WALK from this module for its slider.
    from . import walk_key
    if not pack.carries("Movement"):
        return GAME_WALK
    return min(float(walk_key.speed.value), speeds().walk)
