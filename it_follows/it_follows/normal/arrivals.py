"""What a census does after its first part, in parts an image apart (trial 221, 24 October 2026): the census held the
game 15 to 26 ms every 5 s, 10 to 12 of them the search of every object, which the Hardcore needs (Kevin: « on ne veut
aucune perte pour le hardcore »). The search, the kills counted and the lost let go stay in the census's own image
(enemies.Enemies.look); the new enemies met and given the level, then those held kept, go here, PART_S at most an
image, one enemy at least.

A census's objects hold for its image only (seen.py): an enemy waiting is held by weak pointers, to itself and to its
zone, and met only if the game still says it alive. One dead meanwhile is left: the next census reads its body,
wherever it lies, and counts its kill as before (kills.py does not ask whether it was met).
"""

from collections import deque
from dataclasses import dataclass, replace
import time
from typing import Any, Callable

import unrealsdk

from ..characters import reads

# The census's image already holds its search; each later one takes this much more at most.
PART_S = 0.003


@dataclass(frozen=True)
class Waiting:
    """An enemy a census found, its game objects swapped for weak pointers."""
    seen: Any
    actor: Any
    zone: Any

    @classmethod
    def of(cls, seen: Any) -> "Waiting":
        zone = unrealsdk.unreal.WeakPointer(seen.zone) if seen.zone is not None else None
        return cls(replace(seen, actor=None, zone=None), unrealsdk.unreal.WeakPointer(seen.actor), zone)

    def now(self) -> Any:
        """The enemy as the census read it, with its objects of now; None when gone or no longer said alive."""
        actor = self.actor()
        if actor is None or reads.dead(actor) is not False:
            return None
        return replace(self.seen, actor=actor, zone=self.zone() if self.zone is not None else None)


class Arrivals:
    """arrive(seen) meets one new enemy, keep(met) keeps one held; clock: seconds, for PART_S."""

    def __init__(self, arrive: Callable[[Any], None], keep: Callable[[Any], None],
                 clock: Callable[[], float] = time.perf_counter) -> None:
        self.arrive, self.keep, self.clock = arrive, keep, clock
        self.waiting: deque[Waiting] = deque()
        self.held: deque[Any] = deque()
        self.gone = 0

    def start(self, new: list, held: list) -> None:
        """A census's new enemies (seen.Seen, nearest first) and those it holds, in place of what the last left."""
        self.waiting = deque(Waiting.of(seen) for seen in new)
        self.held = deque(held)
        self.gone = 0

    def pending(self) -> bool:
        return bool(self.waiting or self.held)

    def part(self) -> None:
        """The new first, then the held, until PART_S passed."""
        began = self.clock()
        while self.pending():
            if self.waiting:
                seen = self.waiting.popleft().now()
                if seen is None:
                    self.gone += 1
                else:
                    self.arrive(seen)
            else:
                self.keep(self.held.popleft())
            if self.clock() - began >= PART_S:
                return

    def clear(self) -> None:
        self.waiting.clear()
        self.held.clear()
