"""The recruiter: every EVERY_S during a run, the census's enemies around the hunter not yet in the horde are chosen to
join it, in the place of those the game took back. Read only: the horde draws them.

Why (decision 36, applying Kevin's decision 2: « petit à petit les ennemis finissent tous par arriver sans jamais
s'arrêter »; docs/RUN/enquetes/2026-10-12-arret-au-loin.md, trials 6q and 6r): the trials drew the enemies once, at
the start, and the game took them all back some 450 to 670 m from where they came. The enemies standing where the
hunter now is come instead.
"""

import math
import time
from typing import Any, Callable

from . import census
from .seen import Seen

# A census a while: often enough that the horde fills again within a few seconds of a loss.
EVERY_S = 5.0
# Each census reads for at most this long: the game waits for it, where the census of a run's start may take
# census.MAX_SECONDS.
READ_S = 0.25


class Recruiter:
    """Chooses, once every EVERY_S, the enemies to draw. No cap on how many join a run, where the trials stopped at 600:
    a run may last an hour or more, and what It Follows keeps about an enemy is forgotten when it is lost
    (docs/RUN/plan-etape-2-coeur.md)."""

    def __init__(self, now: float) -> None:
        self.read_at = now
        # How many joined this run, for the log only.
        self.joined = 0

    def due(self, now: float) -> bool:
        """Whether a census is due, and if so counted as made now."""
        if now - self.read_at < EVERY_S:
            return False
        self.read_at = now
        return True

    def choose(self, player: Any, here: tuple | None, taken: set[str], room: int,
               known: frozenset[str] | set[str] = frozenset(), keep: Callable[[Seen], bool] | None = None
               ) -> tuple[list[Seen], dict, census.Sighting]:
        """The enemies kept around the hunter that are not taken, nearest first, at most room, and only those keep
        says yes to when given; with what the census read, kept, passed over and why, and took in time; and who it saw
        alive and dead. Why the reasons are said (trial 8e): in trial 8d, 80 enemies handed to It Follows' camps never
        joined the horde, nor were their camps free again. known: the horde's own, read alive and no further
        (census.seen_around)."""
        began = time.monotonic()
        found, stats, sighting = census.seen_around(player, READ_S, known=known)
        free = [seen for seen in found if seen.name not in taken and seen.at is not None and here is not None
                and (keep is None or keep(seen))]
        free.sort(key=lambda seen: math.dist(seen.at, here))
        chosen = free[:max(0, room)]
        self.joined += len(chosen)
        said = {"read": stats["read"], "kept": stats["kept"], "skipped": stats["skipped"], "stopped": stats["stopped"],
                "took_ms": round((time.monotonic() - began) * 1000.0, 1)}
        return chosen, said, sighting
