"""The kinds of the game's own enemies met around the hunter during a run, for the killed to come back as enemies of the
place (decision 56: « un ennemi de la zone s'il y en a »).

Each census (recruit.py) says the name, kind, zone and place of every enemy it kept. An enemy of the horde holds the
zone It Follows lends, whose camp is one It Follows made, and a copy holds its own camp's zone, made by It Follows too:
both are left out, so that what is kept is the game's enemies, met before they join. Each one is remembered for the
run where it was last met (decision 68), and the kinds of the place are those met within PLACE_M of the hunter, one
entry per enemy, so that they come back in the share the place held them, taken in turn. With none met within PLACE_M,
the killed one comes back as it was (wave.py), as before decision 56.

Why remembered, and not only the last census's kinds (trials 14 and 15): back by fast travel at the place of the
run's start, the census met none of the game's enemies there for 3 minutes, and the killed came back as the kinds of
the place left 16 km away, then as themselves. Crossing an empty stretch, the kinds met within PLACE_M still come back.
"""

import math
from typing import Callable, Iterable

# The place the hunter stands in: the game's camps wake within 80 to 300 m of him (trial 6u).
PLACE_M = 300.0
# The enemies remembered at most, the one met longest ago forgotten first.
MOST = 2000
# Where none was met, Kevin's rule (guard.py) asks the kinds of the enemies met last anywhere: about a place's worth.
LATEST = 20


def camp_of(path: str) -> str:
    """The name of the object owning a zone, read from the zone's path: a camp's zone is its spawner's part,
    …PersistentLevel.OakSpawner_2147458310.Territory. Empty for an enemy without a zone."""
    parts = path.rsplit(".", 2)
    return parts[-2] if len(parts) == 3 else ""


class ZoneKinds:
    """Where each of the game's enemies was last met, by name, and whose turn is next."""

    def __init__(self) -> None:
        self.met: dict[str, tuple[str, tuple]] = {}
        self.turn = 0
        # How many the last census met, for the status line.
        self.last = 0

    def saw(self, kept: Iterable[tuple], ours: Callable[[str], bool]) -> int:
        """kept: (name, kind, zone path, place) of each enemy a census kept. The game's enemies among them, those
        whose zone's camp is not one It Follows made, are remembered where they stand; how many were met."""
        self.last = 0
        for name, kind, path, at in kept:
            if not kind or at is None or ours(camp_of(path)):
                continue
            self.met.pop(name, None)
            self.met[name] = (kind, at)
            self.last += 1
        while len(self.met) > MOST:
            del self.met[next(iter(self.met))]
        return self.last

    def _near(self, here: tuple | None) -> list[str]:
        if here is None:
            return []
        reach = PLACE_M * 100.0
        return [kind for kind, at in self.met.values() if math.dist(at, here) <= reach]

    def around(self, here: tuple | None, knows: Callable[[str], bool]) -> list[str]:
        """The kinds of the place: one entry per enemy met within PLACE_M of here, those It Follows' camps can make."""
        return [kind for kind in self._near(here) if knows(kind)]

    def latest(self, knows: Callable[[str], bool]) -> list[str]:
        """The kinds of the enemies met last anywhere in the run, the latest first, at most LATEST, those It Follows'
        camps can make."""
        return [kind for kind, _at in reversed(self.met.values()) if knows(kind)][:LATEST]

    def pick(self, killed: str, around: list[str]) -> str:
        """The kind the next one comes back as: the next of the place's kinds (around()), else the killed one's own."""
        if not around:
            return killed
        kind = around[self.turn % len(around)]
        self.turn += 1
        return kind

    def gauge(self, here: tuple | None) -> dict:
        """What a status line writes: the kinds met within PLACE_M of here, how many of the game's enemies the last
        census met, and how many are remembered."""
        return {"kinds": len(set(self._near(here))), "met_last": self.last, "remembered": len(self.met)}
