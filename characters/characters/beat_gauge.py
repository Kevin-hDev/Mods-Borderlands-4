"""What a beat measures of itself for its status line: how many times the game called its hook, what a call with
nothing to do took in it, and the images a second the player saw (decision 102 of docs/RUN, audit of 24 October 2026).

The images a second come from the engine's count of images (reads.frame_count), read once a second: over the span
since the last line, and the lowest of its seconds. A span longer than LONGEST_SPAN_S held a pause or a load, where
the beat stands still while the game draws on, and is left out. Moved here from It Follows' run_gauge.py, so that the
team's status line, Companions' too, counts them the same way.
"""

import time
from time import perf_counter
from typing import Callable

LONGEST_SPAN_S = 2.0


class Calls:
    """A hook's calls since the last line, and the seconds the calls with nothing to do took; clock() the beat's
    time. What the SDK spends handing each call to Python is not in it (trial 40 of docs/RUN: about 2.5 µs)."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self.clock = clock
        self.calls, self.idle_calls, self.idle_s = 0, 0, 0.0
        self.counted_at = clock()

    def called(self) -> float:
        """One call counted: the moment it began, for idle()."""
        self.calls += 1
        return perf_counter()

    def idle(self, began: float) -> None:
        """The call that began then had nothing to do."""
        self.idle_calls += 1
        self.idle_s += perf_counter() - began

    def said(self) -> dict:
        """The calls a second, and the µs a call with nothing to do took (None without one); then counted afresh."""
        moment = self.clock()
        spent = moment - self.counted_at
        said = {"hook_calls_s": round(self.calls / spent, 1) if spent > 0.0 else 0.0,
                "hook_idle_us": round(self.idle_s / self.idle_calls * 1e6, 2) if self.idle_calls else None}
        self.calls, self.idle_calls, self.idle_s, self.counted_at = 0, 0, 0.0, moment
        return said


class FrameRate:
    """The images a second, from the engine's count read once a second (read)."""

    def __init__(self) -> None:
        # The image count and the moment last read; the images and seconds counted since the last line.
        self.counted: tuple[int, float] | None = None
        self.images, self.image_s = 0, 0.0
        self.lowest: float | None = None

    def read(self, count: int | None, now: float) -> None:
        """The engine's image count read at now, None when unread: the span since the last read counted."""
        if count is not None and self.counted is not None:
            images, span = count - self.counted[0], now - self.counted[1]
            if 0.0 < span <= LONGEST_SPAN_S and images >= 0:
                self.images += images
                self.image_s += span
                rate = images / span
                self.lowest = rate if self.lowest is None else min(self.lowest, rate)
        self.counted = None if count is None else (count, now)

    def said(self) -> dict:
        """The images a second over the spans counted and the lowest second (None when none was), then counted
        afresh from the last count."""
        said = {"fps": round(self.images / self.image_s, 1) if self.image_s > 0.0 else None,
                "fps_low": None if self.lowest is None else round(self.lowest, 1)}
        self.images, self.image_s, self.lowest = 0, 0.0, None
        return said
