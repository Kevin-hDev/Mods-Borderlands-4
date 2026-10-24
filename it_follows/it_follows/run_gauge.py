"""What a run measures of itself (spec, section 6, « Les traces »): the longest its second took, each task put off to
the images after it (frame.Beat.defer), and the images a second the player saw (decision 102,
characters/beat_gauge.py), written in the status line every STATUS_EVERY_S and then counted afresh. A second or a task
that holds the game longer than SLOW_S is written at once: a freeze each second is no game. The normal mode measures
itself the same way (normal/play.py, audit of 24 October 2026), under its own events' names.
"""

from typing import Any, Callable

from .characters import beat_gauge

SLOW_S = 0.5
STATUS_EVERY_S = 30.0


class Gauge:
    """note(event, **fields) writes a line; the first status line comes STATUS_EVERY_S after now. slow: the events of
    a second and of a task that held the game too long."""

    def __init__(self, note: Callable[..., None], now: float,
                 slow: tuple[str, str] = ("slow_sample", "slow_task")) -> None:
        self.note, self.slow = note, slow
        self.next_status = now + STATUS_EVERY_S
        self.slowest_ms = 0.0
        self.tasks_ms: dict[str, float] = {}
        self.rate = beat_gauge.FrameRate()

    def second(self, took_ms: float, **context: Any) -> None:
        """context: what the line about a slow second says beside its time (the horde's size, the enemies held)."""
        self.slowest_ms = max(self.slowest_ms, took_ms)
        if took_ms > SLOW_S * 1000.0:
            self.note(self.slow[0], took_ms=round(took_ms, 1), **context)

    def task(self, name: str, took_ms: float, **context: Any) -> None:
        self.tasks_ms[name] = max(self.tasks_ms.get(name, 0.0), took_ms)
        if took_ms > SLOW_S * 1000.0:
            self.note(self.slow[1], task=name, took_ms=round(took_ms, 1), **context)

    def frames(self, count: int | None, now: float) -> None:
        """The engine's image count read at now, None when unread."""
        self.rate.read(count, now)

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
                "tasks_ms": {name: round(ms, 1) for name, ms in self.tasks_ms.items()}, **self.rate.said()}
        self.slowest_ms, self.tasks_ms = 0.0, {}
        return said
