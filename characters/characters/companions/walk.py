"""Reinforcements, trial 136: a character told to walk to the hunter when he stands far, the walk aborted once it
arrives. It Follows' order (it_follows/chaser.py), with its repaired walk (it_follows/brain_walk.py: AIScriptedMove
through the SDK's process_event, blocks never freed; two crashes in three launches before the repair, none since,
docs/RUN/enquetes/2026-10-10-marche-reparee.md), handed to the Walker as brain, never copied: one authority.
It Follows walks enemies from 75 m and aborts within 35 m; a reinforcement keeps closer, hence WALK_M and ARRIVAL_M.

Since trial 166, it stops farther and is checked more often (Kevin, 20 October 2026: « il se rapproche trop … ils
viennent coller le chasseur donc plus d'espace »). Checked once a second, a walk aborted within 5 m had run a second
nearer first: 5.5 m, then 1.7 m a second later, where it stayed (20:46:24). Vex Phase Clones checks its walks at each
beat and stops them within 6.25 m (vex_phase_clones/walk.py, STOP_M, the game's own orbit of a companion); here the
follow asks arrive() every ARRIVAL_EVERY_S while it walks.

Since trial 168, within PUSH_M of the hunter the companion is pushed to its own place on the ARRIVAL_M circle
(push.py), as Vex walks its Specters, instead of walked to the hunter himself; farther, the game's walk goes
around what stands in the way, which a push in a straight line does not, and is turned into a push once within
PUSH_M. live() says whether the walk still moves it, for the follow to tell a blocked one (stuck.py).
"""

from typing import Any, Callable

WALK_M = 15.0
# 8 m at trial 167, its walks stopping at 7 to 8 m; then Kevin, 20 October 2026: « on va passer a 10m et ce sera tres
# bien comme ça ».
ARRIVAL_M = 10.0
# The last 10 m of a walk pushed, as Vex pushes its whole walk: enough for each to reach its own place.
PUSH_M = 20.0
# A run of 5.8 m/s at most near the hunter (4.8 with the bonus of 1.2, trial 138) goes 1.2 m in this long.
ARRIVAL_EVERY_S = 0.2
# It Follows' trial 6d: the game ends most walks by itself within seconds; one is given again at most this often.
REWALK_EVERY_S = 5.0
MAX_TEXT = 60


class Walker:
    """One character's walks to the hunter: actor is its weak pointer; note(text) says a call before it is made; brain
    is It Follows' brain_walk module; push (push.Push) pushes it to its place, turn degrees off its own side (its
    rank's step of the fan)."""

    def __init__(self, actor: Any, name: str, note: Callable[[str], None], brain: Any, push: Any,
                 turn: float = 0.0) -> None:
        self.actor, self.name, self.note, self.brain, self.push, self.turn = actor, name, note, brain, push, turn
        self.walking, self.block, self.walked_at = False, None, 0.0
        self.walks = self.pushed = 0

    def _walk(self, goal: Any, pc: Any, now: float) -> None:
        """Counted as walking before the call, so that a failing one is aborted all the same."""
        self.note(f"about to call AIScriptedMove on {self.name}")
        self.walking, self.walked_at = True, now
        self.walks += 1
        self.block = self.brain.walk(self.actor(), goal, pc)

    def _push(self, here: tuple, at: tuple) -> None:
        self.walking = True
        self.pushed += 1
        self.push.begin(here, at, self.turn)

    def keep(self, to_hunter: float | None, goal: Any, pc: Any, now: float, here: tuple | None = None,
             at: tuple | None = None) -> str:
        """Once a sample: beyond WALK_M, pushes it to its place within PUSH_M, else walks it to the hunter, the game's
        walk turned into a push once within PUSH_M; aborts the walk within ARRIVAL_M, gives the game's walk again once
        the game ended it before the arrival; says what it did. A failing walk raises."""
        if to_hunter is None or goal is None:
            return "unknown"
        arrived = self.arrive(to_hunter)
        if arrived is not None:
            return arrived
        pushable = to_hunter <= PUSH_M and here is not None and at is not None
        if not self.walking:
            if to_hunter <= WALK_M:
                return "near"
            if pushable:
                self._push(here, at)
                return "push"
            self._walk(goal, pc, now)
            return "walk"
        if self.push.active:
            return "pushing"
        if pushable:
            stopped = self.stop()
            self._push(here, at)
            return f"push:{stopped}"
        if self.brain.ended(self.block) and now - self.walked_at >= REWALK_EVERY_S:
            self._walk(goal, pc, now)
            return "walk_again"
        return "walking"

    def step(self, here: tuple | None, at: tuple | None, to_hunter: float | None) -> str | None:
        """Between samples, while pushed: one push toward its place, or the arrival within ARRIVAL_M, said."""
        if not self.push.active or here is None or at is None:
            return None
        arrived = self.arrive(to_hunter)
        if arrived is None:
            self.push.step(here, at, ARRIVAL_M)
        return arrived

    def live(self) -> bool:
        """Whether a walk is meant to move it now: pushed, or the game's walk not ended yet."""
        return self.walking and (self.push.active or not self.brain.ended(self.block))

    def arrive(self, to_hunter: float | None) -> str | None:
        """The walk aborted once it is within ARRIVAL_M, said; None while it goes on, or when there is no walk."""
        if not self.walking or to_hunter is None or to_hunter > ARRIVAL_M:
            return None
        return f"arrived:{self.stop()}"

    def outcome(self) -> str | None:
        """What the game last wrote in the latest walk's Exec, if it was ever walked."""
        return None if self.block is None else str(self.brain.outcome(self.block))[:MAX_TEXT]

    def stop(self) -> str:
        """Ends the walk: a push by giving no more, the game's walk by aborting it."""
        if not self.walking:
            return "inactive"
        if self.push.active:
            self.push.end()
            self.walking = False
            return "pushed"
        actor = self.actor()
        if actor is None:
            return "unavailable"
        self.walking = False
        try:
            self.note(f"about to call AbortScriptedBrainTask on {self.name}")
            self.brain.abort(actor)
            return "aborted"
        except Exception as error:
            return f"abort_error:{type(error).__name__}"
