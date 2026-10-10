"""The one writer of the sprint node's backward slot (Run_B), for every camera mod (docs/omni_direction/spec).

The sprint node (GbxAnimGraphNode_Locomotion_2) chooses its forward player (BS_Sprint) or its backward one from the
game's own reference, never more than 75 degrees from the camera, not from a turned body (2026-09-24,
docs/investigations/omni_sprint/2026-09-23-omni-sprint-animation-figee.md). Three uses of that slot:
- FORWARD: the body is held turned toward its run, so it always runs forward: the slot gets the forward sprint (trial 6,
  2026-10-09, Kevin: « ça fonctionne nickel »);
- CARRIER: the body faces the camera and the sprint is open: Omni Sprint's private backward run (backward_carrier.py)
  when sprinting backward, as Omni Sprint did alone before;
- NONE: the slot as the game leaves it, empty.
"""

from typing import Any, Callable

FORWARD, CARRIER, NONE = "forward", "carrier", "none"
# Forward writes said one by one, then only counted: a game that empties the slot every frame must not flood the log.
MAX_SAID = 5


class SprintSlot:
    def __init__(self, carrier: Any, players: Callable[[Any], Any], same: Callable[[Any, Any], bool],
                 weak: Callable[[Any], Any], log: Callable[[str], None]) -> None:
        self.carrier, self.players, self.same, self.weak, self.log = carrier, players, same, weak, log
        # Held weakly: after a map change the old body may be destroyed, and calling it would be undefined.
        self.anim_ref: Any = None
        self.anim_id = 0
        self.writes = 0
        self.holding = False
        self.left_alone_id = 0

    def update(self, character: Any, anim: Any, anim_id: int, use: str, now_ns: int) -> None:
        if anim_id != self.anim_id:
            # A new body starts with the game's own slot: the old one is never touched again.
            self.anim_ref, self.anim_id, self.holding = self.weak(anim), anim_id, False
        if use == FORWARD:
            if self.carrier.owner is not None:
                self.carrier.stop()
            self._keep_forward(anim)
            return
        self._release_forward()
        if use == CARRIER:
            self.carrier.update(character, anim, now_ns)
        else:
            self.carrier.stop()

    def _keep_forward(self, anim: Any) -> None:
        if self.anim_id == self.left_alone_id:
            return
        try:
            forward, backward = self.players(anim)
            source, current = forward.BlendSpace, backward.BlendSpace
            self.holding = True
            if source is None or self.same(current, source):
                return
            backward.BlendSpace = source
        except (AttributeError, TypeError, ValueError) as exc:
            # The sprint keeps the game's animation for this body; the body still turns.
            self.left_alone_id, self.holding = self.anim_id, False
            self.log(f"sprint slot left alone for this body: {type(exc).__name__}")
            return
        self.writes += 1
        if self.writes <= MAX_SAID:
            self.log(f"forward sprint put in the backward slot, write {self.writes}")

    def _release_forward(self) -> None:
        """Empties the slot again if it still holds the forward sprint this unit put there."""
        anim = self.anim_ref() if self.anim_ref is not None and self.holding else None
        self.holding = False
        if anim is None:
            return
        forward, backward = self.players(anim)
        if backward.BlendSpace is not None and self.same(backward.BlendSpace, forward.BlendSpace):
            backward.BlendSpace = None

    def stop(self) -> None:
        errors = []
        for action in (self._release_forward, self.carrier.stop):
            try:
                action()
            except Exception as error:
                errors.append(error)
        if self.writes > MAX_SAID:
            self.log(f"forward sprint writes this session: {self.writes}")
        self.anim_ref, self.anim_id, self.writes, self.holding = None, 0, 0, False
        if errors:
            raise errors[0]
