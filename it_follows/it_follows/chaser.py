"""One enemy of the horde drawn to the hunter and kept on him: lent the zone posed on him (hunter_zone), the hunter
imposed as its target (target), its brain told to walk to him when it stands far (brain_walk) and the walk aborted
once it arrives; when it is let go, what it still holds is given back.

The recipe of trials 3a and 3c (docs/RUN/enquetes/2026-10-10-zone-qui-suit.md), applied to each enemy since trial 6a;
trial 6b adds the relaunch: the walk given again once the hunter has gone far, the hunter imposed again once the game
cleared the target (docs/RUN/enquetes/2026-10-10-relance.md); trial 6e gives the walk again once the game ended it
(docs/RUN/enquetes/2026-10-10-marche-reparee.md). A failure stays the enemy's own: it is left to its normal life and
the others go on (docs/RUN/spec-run.md, section 6). Flyers are drawn too (trial 6r): never told to walk, the brain's
walk being a walk on the ground; the zone and the target are theirs as for the others.
"""

from typing import Any, Callable

import unrealsdk

from .characters import brain_walk, reads, target

# Trial 2 quinquies: the walk aborted within 35 m, the enemy fights the hunter instead of sticking to him.
ARRIVAL_M = 35.0
# Without a walk, enemies beyond about 75 m froze (trials 2 bis and 3b) and trial 6a's stopped closing in at 200 m; the
# walk given again past 75 m starts before either. Above ARRIVAL_M, so that an arrived enemy is not walked at once.
REWALK_M = 75.0
# Trial 6d: the game ended seven walks of nine itself, 1 to 16 s after giving them, most within 3 s while the hunter
# drove, and the enemy then mostly stood still. Given again at most this often, an enemy is never left without a walk
# much more than 5 s, under the 20 s trials 6a and 6b allowed.
REWALK_EVERY_S = 5.0


class Chaser:
    """One enemy, held through a weak pointer; state: drawn, near (close enough at the start, no walk), flying (never
    walked), walking or arrived; ended: why it is no longer drawn. announce(call, **fields) notes a call before it
    happens."""

    def __init__(self, seen: Any, player_ref: Any, announce: Callable[..., None]) -> None:
        """seen is a seen.Seen; player_ref the hunter's weak pointer."""
        self.name, self.kind, self.announce = seen.name, seen.definition, announce
        self.walks = seen.walks
        self.actor, self.player_ref = unrealsdk.unreal.WeakPointer(seen.actor), player_ref
        self.patch = target.imposed(self.actor, player_ref)
        self.state, self.walking = "drawn", False
        self.ended: str | None = None
        self.block: Any = None
        self.walked_at = 0.0

    def _walk(self, goal: Any, pc: Any, again: bool, now: float) -> None:
        """Counted as walking before the call, so that a failing one is aborted all the same."""
        self.announce("AIScriptedMove", on=self.name, again=again)
        self.walking, self.walked_at = True, now
        self.block = brain_walk.walk(self.actor(), goal, pc)
        self.state = "walking"

    def _given_up(self, now: float) -> bool:
        """Its walk ended by the game, the last one given REWALK_EVERY_S ago or more."""
        return self.block is not None and brain_walk.ended(self.block) and now - self.walked_at >= REWALK_EVERY_S

    def outcome(self) -> str | None:
        """What the game last wrote in its latest walk's Exec, if it was ever walked."""
        return None if self.block is None else brain_walk.outcome(self.block)

    def draw(self, zone: Any, seen: Any, goal: Any, pc: Any, far: bool, now: float) -> str | None:
        """Lends it the zone, imposes the hunter, then walks it to him if far; says why it could not, or nothing."""
        try:
            taken = zone.lend(seen)
        except Exception as error:
            return f"zone_call_failed:{type(error).__name__}"
        if taken != "target":
            return "zone_not_taken"
        self.announce("AISetScriptedTarget", on=self.name)
        try:
            self.patch.apply()
        except Exception as error:
            return f"target_not_taken:{type(error).__name__}"
        if not self.walks:
            self.state = "flying"
            return None
        if not far:
            self.state = "near"
            return None
        try:
            self._walk(goal, pc, False, now)
        except Exception as error:
            return f"order_not_taken:{type(error).__name__}"
        return None

    def check(self, zone: Any) -> tuple[Any, str | None]:
        """The enemy, and why it is lost: gone, dead, taken back by the game (no zone) or given another zone."""
        mover = self.actor()
        if mover is None:
            return None, "mover_gone"
        if reads.dead(mover) is True:
            return mover, "mover_dead"
        which = zone.held(self.name, mover.GetTerritory())
        if which == "none":
            return mover, "mover_parked"
        return mover, None if which == "target" else "zone_changed_by_game"

    def _keep_walking(self, to_player: float | None, goal: Any, pc: Any, now: float) -> dict:
        if to_player is None:
            return {}
        if self.state == "walking" and to_player <= ARRIVAL_M:
            self.state = "arrived"
            return {"walk": self.stop_walk()}
        if self.state != "walking" and to_player > REWALK_M:
            self._walk(goal, pc, True, now)
            return {"walk": "again"}
        if self.state == "walking" and self._given_up(now):
            self._walk(goal, pc, True, now)
            return {"walk": "again_after_end"}
        return {}

    def keep(self, to_player: float | None, goal: Any, pc: Any, impose_again: bool, now: float) -> dict:
        """Once a sample, for an enemy that walks: the walk aborted when it arrives within ARRIVAL_M; given again once
        it is farther than REWALK_M after arriving, or, still farther than ARRIVAL_M, once the game ended it
        (_given_up); with impose_again, the hunter imposed again once the game cleared the target, never over another
        script's. Says what it did. A failing walk raises; a refused target is only said, and tried again at the next
        sample: the game may refuse it while the hunter drives, and letting the enemy go for that would lose the horde
        at the first ride."""
        done = self._keep_walking(to_player, goal, pc, now) if self.walks else {}
        if impose_again and self.patch.read() == "none":
            self.patch = target.imposed(self.actor, self.player_ref)
            self.announce("AISetScriptedTarget", log=False, on=self.name, again=True)
            try:
                self.patch.apply()
                done["target"] = "again"
            except Exception as error:
                done["target"] = f"refused:{type(error).__name__}"
        return done

    def stop_walk(self) -> str:
        if not self.walking:
            return "inactive"
        mover = self.actor()
        if mover is None:
            return "unavailable"
        self.walking = False
        try:
            self.announce("AbortScriptedBrainTask", on=self.name)
            brain_walk.abort(mover)
            return "aborted"
        except Exception as error:
            return f"abort_error:{type(error).__name__}"

    def release(self, zone: Any, reason: str, body_reused: bool) -> dict:
        """Gives back what it still holds, once: its walk, its own zone, its target; nothing is called on a body the
        game reuses."""
        if self.ended is not None:
            return {}
        self.ended = reason
        order = "not_needed" if body_reused else self.stop_walk()
        restoration = zone.give_back(self.name, self.actor(), body_reused)
        cleared = target.release(self.patch, body_reused, lambda: self.announce("AIClearScriptedTarget", on=self.name))
        return {"order": order, "restoration": restoration, "target": cleared}
