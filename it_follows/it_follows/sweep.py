"""The second's pass over the horde, cut into parts of PART enemies, each part in an image of its own (decision 107;
audit of 16 October 2026, A5).

Why: in trials 39 and 40 the second's own image took 10 to 19.5 ms with 100 to 120 enemies, the heaviest of the mod's
images, while the hook's calls cost about 3 µs each, a few ms a second spread over every image (trial 40). The first
part runs in the second's image, each other in an image put off (frame.Beat.defer), which reads again where the hunter
stands and where he looks: he may have moved and turned since. The catch-up's places and traces stay counted by the
second (catch_up.walk, once a second, before the pass). Once the last part is done, the float watch looks, and the
wave is regulated and ticks, as after the whole pass before. A pass not done when the next second comes is begun again
with every enemy, its end not run that second, and counted (cut).
"""

from time import perf_counter
from typing import Any, Callable

from . import wave
from .characters import reads

# 120 enemies, the most a run draws (horde.CROWD_MAX), in four parts.
PART = 30


class Sweep:
    """horde (horde.Horde); parts, the run's pieces, with its catch-up (catch) and its wave; floating
    (float_watch.FloatWatch); defer(name, task) puts a task off to a later image; player() and pc() read the hunter and
    his controller again; timed(name, began) measures a task put off, began read from now(), frame.now."""

    def __init__(self, horde: Any, parts: Any, floating: Any, defer: Callable[[str, Callable[[float], None]], None],
                 player: Callable[[], Any], pc: Callable[[], Any], timed: Callable[[str, float], None],
                 now: Callable[[], float]) -> None:
        self.horde, self.parts, self.floating, self.defer = horde, parts, floating, defer
        self.player, self.pc, self.timed, self.now = player, pc, timed, now
        self.queue: list = []
        self.lines: list[dict] = []
        # Where the horde stood at the end of the last pass (wave.where), for the status line.
        self.horde_at: dict = {}
        # Since the last status line: the most parts of a pass, the longest part's enemies, the passes cut.
        self.parts_most, self.part_ms, self.cut = 0, 0.0, 0
        self.made = 0

    def start(self, player: Any, pc: Any, here: tuple | None, now: float) -> None:
        """The second's pass begun on every enemy drawn, its first part made in this image."""
        if self.queue:
            self.cut += 1
        self.queue, self.lines, self.made = self.parts.catch.queue(self.horde.drawn()), [], 0
        self._part(player, pc, here, now)

    def _next(self, now: float) -> None:
        """The next part, in an image of its own: the hunter, his place and where he looks read again. Without him,
        the pass is dropped; the second's own tick says why."""
        player = self.player()
        if player is None:
            self.queue = []
            return
        began = self.now()
        pc = self.pc()
        self.parts.catch.look(pc)
        self._part(player, pc, reads.point(player), now)
        self.timed("sweep", began)

    def _part(self, player: Any, pc: Any, here: tuple | None, now: float) -> None:
        taken, self.queue = self.queue[:PART], self.queue[PART:]
        began = perf_counter()
        self.lines += self.horde.sample(taken, player, pc, here, now)
        self.part_ms = max(self.part_ms, (perf_counter() - began) * 1000.0)
        self.made += 1
        self.parts_most = max(self.parts_most, self.made)
        if self.queue:
            self.defer("sweep", self._next)
            return
        self.floating.look(self.horde.chasers, now)
        self.parts.wave.regulate(wave.near(self.lines), len(self.lines))
        self.horde_at = wave.where(self.lines)
        self.parts.wave.tick(player, pc, here, now)

    def gauge(self) -> dict:
        """Since the last time asked: the most parts of a pass, the longest part's enemies in ms, the passes cut
        short; then counted afresh."""
        said = {"parts": self.parts_most, "part_ms": round(self.part_ms, 1), "cut": self.cut}
        self.parts_most, self.part_ms, self.cut = 0, 0.0, 0
        return said
