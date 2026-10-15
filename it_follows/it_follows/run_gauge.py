"""What a run measures of itself (spec, section 6, « Les traces »): the longest its second took, and each task put
off to the images after it (frame.Beat.defer), written in the status line every STATUS_EVERY_S and then counted
afresh. A second or a task that holds the game longer than SLOW_S is written at once: a freeze each second is no game.
"""

from typing import Callable

SLOW_S = 0.5
STATUS_EVERY_S = 30.0


class Gauge:
    """note(event, **fields) writes a line; the first status line comes STATUS_EVERY_S after now."""

    def __init__(self, note: Callable[..., None], now: float) -> None:
        self.note = note
        self.next_status = now + STATUS_EVERY_S
        self.slowest_ms = 0.0
        self.tasks_ms: dict[str, float] = {}

    def second(self, took_ms: float, horde: int) -> None:
        self.slowest_ms = max(self.slowest_ms, took_ms)
        if took_ms > SLOW_S * 1000.0:
            self.note("slow_sample", took_ms=round(took_ms, 1), horde=horde)

    def task(self, name: str, took_ms: float, horde: int) -> None:
        self.tasks_ms[name] = max(self.tasks_ms.get(name, 0.0), took_ms)
        if took_ms > SLOW_S * 1000.0:
            self.note("slow_task", task=name, took_ms=round(took_ms, 1), horde=horde)

    def status_due(self, now: float) -> bool:
        """Whether a status line is due, and if so the next one STATUS_EVERY_S later."""
        if now < self.next_status:
            return False
        self.next_status = now + STATUS_EVERY_S
        return True

    def spent(self) -> dict:
        """The longest second and each task's longest since the last status line, then counted afresh."""
        said = {"slowest_ms": round(self.slowest_ms, 1),
                "tasks_ms": {name: round(ms, 1) for name, ms in self.tasks_ms.items()}}
        self.slowest_ms, self.tasks_ms = 0.0, {}
        return said
