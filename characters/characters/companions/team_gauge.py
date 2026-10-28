"""What the team's beat costs, written every STATUS_EVERY_S while a team runs (audit of 24 October 2026): its hook's
calls a second and what a call with nothing to do took (beat_gauge.Calls), the beats that had work, the time they took
a second and the longest, each of its parts apart (the follows, the clothes, those on their way, the bars), and the
images a second the player saw (beat_gauge.FrameRate), the engine's count read once a second. Before it, the team
wrote no time of its own: trial 219 counted its hook's calls only in the Horde's line.
"""

import time
from time import perf_counter
from typing import Callable

from .. import beat_gauge, reads

STATUS_EVERY_S = 30.0
FRAMES_EVERY_S = 1.0


class TeamGauge:
    """clock() the team's time; the first line comes STATUS_EVERY_S after it is made."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self.clock = clock
        self.since = clock()
        self.next_status, self.next_frames = self.since + STATUS_EVERY_S, self.since
        self.calls = beat_gauge.Calls(clock)
        self.rate = beat_gauge.FrameRate()
        self.worked, self.busy_s, self.longest_s = 0, 0.0, 0.0
        # Within the beats that had work, each of the team's parts by its name, a dozen at most (team.py and
        # follow.py name them): the seconds it took, the longest once. Trial 221: the team's work took 6 to 17 ms a
        # second, 40 at trial 220, none said where; trial 222: the follows three quarters of it.
        self.parts: dict[str, list[float]] = {}
        self.marked = perf_counter()

    def mark(self) -> None:
        """The moment the next part begins."""
        self.marked = perf_counter()

    def part(self, name: str) -> None:
        """The part named ended now, begun at the last mark; the next begins."""
        ended = perf_counter()
        took, self.marked = ended - self.marked, ended
        tally = self.parts.setdefault(name, [0.0, 0.0])
        tally[0] += took
        tally[1] = max(tally[1], took)

    def called(self) -> float:
        """A call of the hook counted: the moment it began."""
        return self.calls.called()

    def idle(self, began: float) -> None:
        """The call that began then had nothing to do."""
        self.calls.idle(began)

    def done(self, began: float, now: float) -> dict | None:
        """A beat that had work, begun at began (perf_counter), at the team's time now: counted, the image count read
        when a second passed; the line's fields when one is due, then counted afresh; None otherwise."""
        took = perf_counter() - began
        self.worked += 1
        self.busy_s += took
        self.longest_s = max(self.longest_s, took)
        if now >= self.next_frames:
            self.next_frames = now + FRAMES_EVERY_S
            self.rate.read(reads.frame_count(), now)
        if now < self.next_status:
            return None
        span = now - self.since
        said = {**self.calls.said(), "worked_s": round(self.worked / span, 1) if span > 0.0 else 0.0,
                "busy_ms_s": round(self.busy_s * 1000.0 / span, 3) if span > 0.0 else 0.0,
                "longest_ms": round(self.longest_s * 1000.0, 2), **self.rate.said(),
                "parts_ms_s": {name: round(seconds * 1000.0 / span, 3) if span > 0.0 else 0.0
                               for name, (seconds, _) in self.parts.items()},
                "parts_longest_ms": {name: round(longest * 1000.0, 2) for name, (_, longest) in self.parts.items()}}
        self.since, self.next_status = now, now + STATUS_EVERY_S
        self.worked, self.busy_s, self.longest_s = 0, 0.0, 0.0
        self.parts = {}
        return said
