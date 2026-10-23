"""Reinforcements, trial 168: whether a walking companion still gets anywhere, as Vex Phase Clones tells a blocked
Specter (vex_phase_clones/stuck.py): one walked against a rock walks on the spot forever (Kevin, 2026-10-12, of a
Specter: « il est bloqué à avancer contre des rochers … et il s'arrête pas »). Less than MIN_MOVED_M on the ground in
STUCK_S while its walk is meant to move it is no walk: the follow then teleports it to its place behind the hunter
(catch.py, unstick), as Vex does.
"""

import math
from typing import Callable

MIN_MOVED_M = 1.0
# Vex's four beats of 0.5 s: a short halt on a slope or at a corner is not taken for a blocked walk.
STUCK_S = 2.0


class Stuck:
    """Where the companion last moved from, and since when it has stood there."""

    def __init__(self) -> None:
        self.since: tuple | None = None

    def forget(self) -> None:
        self.since = None

    def blocked(self, at: tuple | None, now: float) -> bool:
        """Whether it has not moved MIN_MOVED_M, flat, in STUCK_S; a place unread counts as moving."""
        if at is None:
            self.since = None
            return False
        if self.since is None or math.hypot(at[0] - self.since[0][0], at[1] - self.since[0][1]) >= MIN_MOVED_M * 100.0:
            self.since = (at, now)
            return False
        return now - self.since[1] >= STUCK_S

    def unstick(self, walking: bool, fighting: bool, at: tuple | None, now: float, teleport: Callable[[], str]) -> str:
        """A walk meant to move it (walking) that has not moved it for STUCK_S, out of a fight, ended by teleport(),
        to its place behind the hunter (catch.py): stuck: and what teleport said; near when none is due. Moved
        here from follow.py at trial 183."""
        if not walking or fighting:
            self.forget()
            return "near"
        if not self.blocked(at, now):
            return "near"
        return f"stuck:{teleport()}"
