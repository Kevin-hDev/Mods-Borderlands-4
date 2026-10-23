"""The enemies a co-op guest's game holds near its hunter (decision 129): its own copies of the host's enemies, which
the host's mod speeds up on the host only. Trial 71: the guest's copies keep the game's 1.0 where the host wrote 1.4,
and given 1.4 by a probe they ran as on the host (docs/RUN/sondes/run_coop_guest_speed_write.py, vérifié en jeu).

Read only. The guest's game names every character OakCharacter_…, its enemies too (trial 71): a player is one holding a
PlayerState, an enemy one whose definition It Follows' table calls an enemy or a boss (kinds.py; whether the guest's
copies hold their definition is to be read in game, each passed over counted by why). A death the game does not say is
no death: trial 71 read none said on the guest's copies. Found as the census finds them (reads.search, the world's
actors), bounded by MAX_SCAN characters and MAX_SECONDS.
"""

import time
from itertools import islice
from typing import Any

from .. import census, kinds
from ..characters import reads

MAX_SCAN = 400
MAX_SECONDS = 0.5
# Farther than the guest sees an enemy run, nearer than the census reads on the host.
NEAR_M = 200.0


def _why_not(actor: Any, player: Any) -> str | None:
    """Why the character is no enemy to speed up, None when it is one."""
    if actor == player or str(getattr(actor, "Name", "")).startswith("Default__"):
        return "self"
    if getattr(actor, "PlayerState", None) is not None:
        return "player"
    if reads.dead(actor) is True:
        return "dead"
    read = kinds.kind(reads.definition(actor))
    if read is None:
        return "unknown_kind"
    return None if read[0] in (kinds.ENEMY, kinds.BOSS) else "other"


def scan(player: Any, here: tuple | None) -> tuple[list[tuple[float, str, Any]], dict[str, int]]:
    """The enemies within NEAR_M, nearest first, as (metres, name, actor); how many were passed over, by why, and
    which way they were found."""
    found: list[tuple[float, str, Any]] = []
    actors, way = reads.search(census.CHARACTER_CLASS, player)
    left: dict[str, Any] = {"way": way}
    began = time.monotonic()
    for actor in islice(actors, MAX_SCAN):
        if time.monotonic() - began > MAX_SECONDS:
            left["time_limit"] = left.get("time_limit", 0) + 1
            break
        why = _why_not(actor, player)
        metres = reads.metres(reads.point(actor), here) if why is None else None
        if why is None and metres is None:
            why = "unplaced"
        elif why is None and metres > NEAR_M:
            why = "far"
        if why is not None:
            left[why] = left.get(why, 0) + 1
            continue
        found.append((metres, str(actor.Name), actor))
    found.sort(key=lambda entry: entry[0])
    return found, left
