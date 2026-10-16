"""The enemies of the horde standing in the air, watched for the log only. Trial 15: Kevin saw beasts born at his
height beside a bridge, walking on the air; decision 72 keeps the trace from taking a character for the ground, and
this watch says whether any enemy still floats, and where it came from.

Each sample, the next PER_SAMPLE walking enemies of the horde in turn are traced under (ground.py): one whose feet
stand more than ABOVE_M above what the trace meets, or above nothing down to DOWN_M, while it neither falls nor flies,
floats; one standing on a character or a projectile is counted apart. The status line says how many were looked at
and how many floated since the last one, with a few of them: kind, movement mode, height, and how long ago the
catch-up last moved it (none: it was born there or walked there).
"""

from typing import Any, Callable

from . import ground, reads

# Two traces a second: with the 120 enemies the horde holds at most (decision 69), each one looked at every 60 s.
# Four, each was looked at between two status lines, for a watch that saw no enemy float in all of trial 33's run
# (audit of 16 October 2026).
PER_SAMPLE = 2
# Higher than an enemy's step down a kerb or a slope under its centre.
ABOVE_M = 1.5
# The ravine under trial 15's bridge; nothing met down to there is floating all the same.
DOWN_M = 30.0
# The floaters a status line names, the first ones looked at.
SHOWN = 5
AIRBORNE = ("MOVE_Falling", "MOVE_Flying")


class FloatWatch:
    """trace is a ground.GroundTrace of its own: a trace that failed stops the watch only. moved_at(name): when the
    catch-up last moved that enemy, or None."""

    def __init__(self, trace: Any, moved_at: Callable[[str], float | None]) -> None:
        self.trace, self.moved_at = trace, moved_at
        self.turn = 0
        self.broken: str | None = None
        self._clear()

    def _clear(self) -> None:
        self.looked, self.floating, self.on_body = 0, 0, 0
        self.floaters: list[dict] = []

    def look(self, chasers: list, now: float) -> None:
        """The next PER_SAMPLE walkers of the horde, in turn."""
        walkers = [chaser for chaser in chasers if chaser.walks]
        for _ in range(min(PER_SAMPLE, len(walkers))):
            if self.broken is not None:
                return
            self._look(walkers[self.turn % len(walkers)], now)
            self.turn += 1

    def _look(self, chaser: Any, now: float) -> None:
        mover = chaser.actor()
        at = reads.point(mover) if mover is not None else None
        mode = reads.mode(mover) if at is not None else None
        if at is None or mode in AIRBORNE:
            return
        # The enemy's own kind keys the half height the trace keeps: as many as there are kinds, never more.
        said, where, _met = self.trace.ground(chaser.kind or chaser.name, mover, at, 0.0, DOWN_M * 100.0)
        if said.startswith("call_failed"):
            self.broken = said
            return
        self.looked += 1
        if said == ground.NOT_WORLD:
            self.on_body += 1
            return
        above_m = None if where is None else (at[2] - where[2] + ground.CLEARANCE_CM) / 100.0
        if said != "no_ground" and (above_m is None or above_m <= ABOVE_M):
            return
        self.floating += 1
        if len(self.floaters) < SHOWN:
            moved = self.moved_at(chaser.name)
            self.floaters.append({"on": chaser.name, "mode": mode,
                                  "above_m": None if above_m is None else round(above_m, 1),
                                  "moved_s_ago": None if moved is None else round(now - moved, 1)})

    def gauge(self) -> dict:
        """What the watch saw since the last status line, then forgotten: above_m None is higher than DOWN_M."""
        said = {"looked": self.looked, "floating": self.floating, "on_body": self.on_body, "floaters": self.floaters}
        if self.broken is not None:
            said["broken"] = self.broken
        self._clear()
        return said
