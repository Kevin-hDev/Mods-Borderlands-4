"""Reinforcements: which character the follow takes (follow.py). Without a spawner, the nearest living one
of the definition, within NEAR_M (trials 135 to 163). Given a spawner, since trial 165, the one that spawner bore: at
trial 164 the nearest was an older one of the same definition, and the companion just made was never followed. A
character's combat zone is owned by the spawner it was born of (trial 164, OakSpawner_2147302639 for both), which is
how it is found.
"""

from typing import Any, Callable

NEAR_M = 60.0


def nearest(characters: list, read: Any, definition: str, here: tuple) -> Any:
    """The living character of that definition closest to the hunter, within NEAR_M; None if there is none."""
    best, best_m = None, NEAR_M
    for actor in characters:
        if read.definition(actor) != definition or read.dead(actor) is True:
            continue
        gap = read.metres(read.place(actor), here)
        if gap is not None and gap <= best_m:
            best, best_m = actor, gap
    return best


def born_of(characters: list, read: Any, zone_of: Callable[[Any], tuple], definition: str, here: tuple,
            spawner: str) -> tuple[Any, Any, str] | None:
    """The living character of that definition within NEAR_M whose zone that spawner owns, with its zone and how the
    zone reads; None if there is none."""
    owner = f" owned by OakSpawner:{spawner}"
    for actor in characters:
        if read.definition(actor) != definition or read.dead(actor) is True:
            continue
        gap = read.metres(read.place(actor), here)
        if gap is None or gap > NEAR_M:
            continue
        zone, text = zone_of(actor)
        if zone is not None and text.endswith(owner):
            return actor, zone, text
    return None


def choose(characters: list, read: Any, zone_of: Callable[[Any], tuple], definition: str, here: tuple,
           spawner: str | None) -> tuple[Any, Any, str]:
    """The character to follow, its zone (None if it has none) and how the zone reads; or None, None and why none."""
    if spawner is not None:
        found = born_of(characters, read, zone_of, definition, here, spawner)
        if found is None:
            return None, None, f"no living {definition} born of {spawner} within {NEAR_M:.0f} m"
        return found
    actor = nearest(characters, read, definition, here)
    if actor is None:
        return None, None, f"no living {definition} within {NEAR_M:.0f} m: spawn it first"
    zone, text = zone_of(actor)
    return actor, zone, text
