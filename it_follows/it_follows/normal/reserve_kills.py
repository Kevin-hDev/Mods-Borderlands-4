"""Throwaway measure (audit of 24 October 2026, M1): where the bodies of the player's kills lie when the census counts
them for the Hardcore. It goes once the census of the normal mode is decided from what the status lines say.

The census of the normal mode still searches every object the game holds (find_all, 9 to 13 ms, decision 105): the
bodies the game puts in its reserve, out of the world, are seen that way alone. Searching the world instead would save
about 10 ms at each census (N3), but would lose a kill whose body left the world before the census and whose enemy was
never met, born and killed between two censuses; nothing tells today how many there are. So at each census that counts
a kill of the player's, the characters of the world are listed too (GameplayStatics.GetAllActorsOfClass, 0.03 to 0.06
ms in trial 38), and each kill is told: its body in the world, or out of it and its enemy met, or out of it and never
met. Should the world's list fail once, nothing more is asked: its stand-in would search every object again.
"""

from itertools import islice
from typing import Any

from .. import census
from ..characters import reads


class ReserveKills:
    def __init__(self) -> None:
        self.counts = dict.fromkeys(("in_world", "out_met", "out_unmet", "unread"), 0)
        self.broken = False

    def add(self, fresh: list[str], player: Any, met: dict | set) -> None:
        """The player's kills a census just counted (kills.Kills.fresh), each told where its body lay; met: the names
        the mode held at that census."""
        if not fresh:
            return
        world = None if self.broken else self._world(player)
        for name in fresh:
            if world is None:
                key = "unread"
            elif name in world:
                key = "in_world"
            else:
                key = "out_met" if name in met else "out_unmet"
            self.counts[key] += 1

    def _world(self, player: Any) -> frozenset[str] | None:
        """The names of the characters in the world in play; None, and never asked again, when it cannot be listed."""
        try:
            actors, way = reads.search(census.CHARACTER_CLASS, player)
            names = (frozenset(reads.clean(getattr(actor, "Name", "")) for actor in islice(actors, census.MAX_SCAN))
                     if way == "actors" else None)
        except Exception:
            names = None
        self.broken = names is None
        return names

    def said(self) -> dict:
        """The kills told since asked last, then counted afresh."""
        said, self.counts = self.counts, dict.fromkeys(self.counts, 0)
        return said
