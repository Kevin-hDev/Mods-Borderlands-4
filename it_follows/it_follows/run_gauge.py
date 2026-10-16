"""What a run measures of itself (spec, section 6, « Les traces »): the longest its second took, each task put off to
the images after it (frame.Beat.defer), and the images a second the player saw (decision 102), written in the status
line every STATUS_EVERY_S and then counted afresh. A second or a task that holds the game longer than SLOW_S is
written at once: a freeze each second is no game.

The images a second come from the engine's count of images, read once a second: over the status line's span, and the
lowest of its seconds. A span longer than LONGEST_SPAN_S held a pause or a load, where the run stands still while the
game draws on, and is left out.
"""

from typing import Callable

SLOW_S = 0.5
STATUS_EVERY_S = 30.0
LONGEST_SPAN_S = 2.0


class Gauge:
    """note(event, **fields) writes a line; the first status line comes STATUS_EVERY_S after now."""

    def __init__(self, note: Callable[..., None], now: float) -> None:
        self.note = note
        self.next_status = now + STATUS_EVERY_S
        self.slowest_ms = 0.0
        self.tasks_ms: dict[str, float] = {}
        # The image count and the moment last read; the images and seconds counted since the last status line.
        self.counted: tuple[int, float] | None = None
        self.images, self.image_s = 0, 0.0
        self.lowest: float | None = None

    def second(self, took_ms: float, horde: int) -> None:
        self.slowest_ms = max(self.slowest_ms, took_ms)
        if took_ms > SLOW_S * 1000.0:
            self.note("slow_sample", took_ms=round(took_ms, 1), horde=horde)

    def task(self, name: str, took_ms: float, horde: int) -> None:
        self.tasks_ms[name] = max(self.tasks_ms.get(name, 0.0), took_ms)
        if took_ms > SLOW_S * 1000.0:
            self.note("slow_task", task=name, took_ms=round(took_ms, 1), horde=horde)

    def frames(self, count: int | None, now: float) -> None:
        """The engine's image count read at now, None when unread: the span since the last read counted."""
        if count is not None and self.counted is not None:
            images, span = count - self.counted[0], now - self.counted[1]
            if 0.0 < span <= LONGEST_SPAN_S and images >= 0:
                self.images += images
                self.image_s += span
                rate = images / span
                self.lowest = rate if self.lowest is None else min(self.lowest, rate)
        self.counted = None if count is None else (count, now)

    def status_due(self, now: float) -> bool:
        """Whether a status line is due, and if so the next one STATUS_EVERY_S later."""
        if now < self.next_status:
            return False
        self.next_status = now + STATUS_EVERY_S
        return True

    def spent(self) -> dict:
        """The longest second, each task's longest and the images a second since the last status line (None when
        none was counted), then counted afresh."""
        said = {"slowest_ms": round(self.slowest_ms, 1),
                "tasks_ms": {name: round(ms, 1) for name, ms in self.tasks_ms.items()},
                "fps": round(self.images / self.image_s, 1) if self.image_s > 0.0 else None,
                "fps_low": None if self.lowest is None else round(self.lowest, 1)}
        self.slowest_ms, self.tasks_ms = 0.0, {}
        self.images, self.image_s, self.lowest = 0, 0.0, None
        return said
