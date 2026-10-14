"""Where each of the grapple gun's gestures is at each frame of a shot: numbers in, phases out, no game here (as
release.py and look_timing.py).

The left arm comes in at the shot and is stretched once its entry is over; it stays stretched while the hook flies.
From the catch it folds as far as the more advanced of the way travelled and the time since the catch over the pull's
foreseen length, never back (docs/apex_grapple/pistolet-grappin/spec-pistolet-grappin.md, section 9, choice 4). The way
travelled alone stays at nothing for up to a second while the player first rises (trial 6,
enquetes/2026-10-04-essais-en-jeu.md): time takes over then. Trial 6 led with one second whatever the pull; the
foreseen length keeps a long pull folding at its own pace, as Kevin asked ("au rythme du trajet en fonction de la
distance", decisions.md, 3 October). The fold never moves faster than a whole one in RUSH_S: an arm still coming in
when the hook bites, or a short fast pull, catches up instead of jumping. At the end the arm finishes its fold at that
pace, then goes out.

The body flies from the catch, its pose following the fold (choice 5); its legs are the game's while the hook flies.
The right weapon goes away at the shot, and comes back RETURN_S before the end the grapple foresees (arrival, anchor
passed, longest pull), or at the end for the others (spec, section 3.3).

Times in ns, as the grapple's clock gives them; lengths in cm.
"""

import math
from dataclasses import dataclass
from typing import NamedTuple

NS_PER_S = 1_000_000_000
# The fastest the arm folds all the way, in seconds.
RUSH_S = 0.3
# How long the right weapon takes to come back: the stow's fade out (the game's own blend, trial 2).
RETURN_S = 0.25
ENTRY, FOLD, EXIT, GONE = "entry", "fold", "exit", "gone"


class Pull(NamedTuple):
    """One frame of the pull, as the grapple sees it."""
    to_anchor: tuple[float, float, float]
    velocity: tuple[float, float, float]


class Pose(NamedTuple):
    """Where the gestures are. `left`: the first-person arm's phase and its fraction; `fold`: how far the fold is, which
    the body's arm and its flight follow; `flight`: None while the legs are the game's; `right_away`: the right
    weapon stowed."""
    left: tuple[str, float]
    fold: float
    flight: float | None
    right_away: bool


@dataclass
class Moves:
    """The gestures of one shot. `entry_s` and `exit_s` are the arm's animation's own."""
    entry_s: float
    exit_s: float
    shot_ns: int
    longest_s: float = 0.0
    caught_ns: int | None = None
    start_gap: float = 0.0
    near: float = 0.0
    foreseen_s: float = 0.0
    ended_ns: int | None = None
    exit_ns: int | None = None
    fold: float = 0.0
    last_ns: int | None = None
    right_away: bool = True

    def catch(self, now_ns: int, start_gap: float, near: float, pull_cap: float) -> None:
        """The hook bites `start_gap` cm from the player; the pull lets go `near` cm from the anchor and adds up to
        `pull_cap` cm/s."""
        if self.caught_ns is None and self.ended_ns is None:
            self.caught_ns, self.start_gap, self.near = now_ns, start_gap, near
            self.foreseen_s = max(0.0, start_gap - near) / pull_cap if pull_cap > 0.0 else 0.0

    def end(self, now_ns: int) -> None:
        if self.ended_ns is None:
            self.ended_ns = now_ns
            self.right_away = False

    def frame(self, now_ns: int, pull: Pull | None = None) -> Pose:
        """The gestures at `now_ns`; called once a frame, in order. `pull` while the pull lasts."""
        step_s = 0.0 if self.last_ns is None else max(0.0, (now_ns - self.last_ns) / NS_PER_S)
        self.last_ns = now_ns
        since_shot_s = (now_ns - self.shot_ns) / NS_PER_S
        if self.ended_ns is not None:
            wanted = 1.0
        elif self.caught_ns is not None:
            wanted = self._wanted(now_ns, pull)
            if pull is not None and self._ends_within(now_ns, pull) <= RETURN_S:
                self.right_away = False
        else:
            wanted = 0.0
        if since_shot_s >= self.entry_s:
            self.fold = max(self.fold, min(wanted, self.fold + step_s / RUSH_S))
        return Pose(self._left(now_ns, since_shot_s), self.fold, self._flight(), self.right_away)

    def _left(self, now_ns: int, since_shot_s: float) -> tuple[str, float]:
        if since_shot_s < self.entry_s:
            return ENTRY, since_shot_s / self.entry_s
        if self.ended_ns is None or self.fold < 1.0:
            return FOLD, self.fold
        if self.exit_ns is None:
            self.exit_ns = now_ns
        out = (now_ns - self.exit_ns) / NS_PER_S / self.exit_s
        return (EXIT, out) if out < 1.0 else (GONE, 1.0)

    def _flight(self) -> float | None:
        return self.fold if self.caught_ns is not None and self.ended_ns is None else None

    def _wanted(self, now_ns: int, pull: Pull | None) -> float:
        since_catch_s = (now_ns - self.caught_ns) / NS_PER_S
        by_time = since_catch_s / self.foreseen_s if self.foreseen_s > 0.0 else 1.0
        by_way = 0.0
        if pull is not None and self.start_gap > self.near:
            gap = math.hypot(*pull.to_anchor)
            by_way = (self.start_gap - gap) / (self.start_gap - self.near)
        return max(0.0, min(1.0, max(by_way, by_time)))

    def _ends_within(self, now_ns: int, pull: Pull) -> float:
        """The seconds left before the end the grapple foresees: arrival, anchor passed or longest pull; infinity when
        none is in sight."""
        left = [math.inf]
        gap = math.hypot(*pull.to_anchor)
        speed_squared = sum(v * v for v in pull.velocity)
        toward = sum(a * v for a, v in zip(pull.to_anchor, pull.velocity))
        if toward > 0.0 and gap > 0.0:
            left.append(max(0.0, gap - self.near) / (toward / gap))
            # The anchor passed: the closest the straight line comes, if it stays farther than the arrival.
            closest_s = toward / speed_squared
            closest = math.dist(pull.to_anchor, tuple(v * closest_s for v in pull.velocity))
            if closest > self.near:
                left.append(closest_s)
        if self.longest_s > 0.0:
            left.append(self.longest_s - (now_ns - self.caught_ns) / NS_PER_S)
        return min(left)
