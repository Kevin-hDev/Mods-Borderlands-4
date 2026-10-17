"""On a co-op host, the rope of each guest who told one: the host pulls the guest as the guest's own game does.

The host moves every player and corrects a guest whose game disagrees; without this, a guest's pull was undone and the
guest put back on the ground (verified in game, docs/coop/2026-10-16-essai-deux-avec-mods.md). So the host plays the
same pull (traction.py) on its own copy of the guest: the anchor found by the same ray, from the guest's character
along the way the guest told (coop_code.py), the hook flying as long, the stick read from the guest's acceleration.

The host's settings are the ones used: the mod's description asks for the same settings on both sides.

The guest's own game decides when its rope lets go and says so: it sees the guest's true moves, the host only those
that have arrived, and the host judging the end itself let go of a rope still pulling on the guest, which then jerked
back (verified in game, trial 4 of docs/coop/2026-10-17-grappin-invite.md). The host keeps the longest pull, so that a
lost message cannot keep a guest pulled; a guest gone, or in a vehicle, ends its rope.
"""

import math
from typing import Any

from unrealsdk.unreal import WeakPointer

from . import aim, coop_code, coop_relay, game, report, settings, traction

FLYING = "flying"
ATTACHED = "attached"
NS_PER_S = 1_000_000_000
# Four players at most in Borderlands 4; the list is bounded all the same, its entries coming from other games.
MAX_GUESTS = 8
# The guest aimed from its camera, the host aims from the guest's character: the ray reaches a little further than the
# range so a shot at its very end still finds its wall.
REACH_SLACK = 1.25
# The guests' lines are written as the player's are, and bounded: they come from other games.
MAX_LINES = 200
# A longest pull of 0 is no limit: a guest swings as long as it likes, and says when it lets go. Should that word be
# lost, the host lets go after the slider's own top, rather than pulling the guest for ever.
NO_WORD_S = 15.0

_ropes: list["GuestRope"] = []
_lines = 0


def _say(text: str) -> None:
    global _lines
    if _lines >= MAX_LINES:
        return
    _lines += 1
    report.note(text if _lines < MAX_LINES else f"{text} (last co-op guest line)")


def remote_stick(character: Any) -> tuple[float, float, float]:
    """The guest's stick as the host knows it: its acceleration over the most it may have. The input the player's own
    pull reads stays empty on the host for a guest (verified in game for Apex Movement, docs/coop/2026-10-17-grimpe-
    invite.md)."""
    movement = character.CharacterMovement
    most = float(movement.MaxAcceleration)
    if most <= 0.0:
        return 0.0, 0.0, 0.0
    pushed = movement.GetCurrentAcceleration()
    x, y = float(pushed.X) / most, float(pushed.Y) / most
    length = math.hypot(x, y)
    if length > 1.0:
        x, y = x / length, y / length
    return x, y, 0.0


class GuestRope:
    def __init__(self, controller: Any) -> None:
        self.pointer = WeakPointer(controller)
        self.name = str(getattr(controller, "Name", "?"))
        self.pending: list[int] = []
        self.state: str | None = None
        self.anchor = (0.0, 0.0, 0.0)
        self.contact_ns = 0
        self.pull: traction.Traction | None = None

    def character(self) -> Any:
        controller = self.pointer()
        pawn = getattr(controller, "Pawn", None) if controller is not None else None
        return pawn if pawn is not None and getattr(pawn, "CharacterMovement", None) is not None else None

    def start(self, character: Any, code: int, now_ns: int) -> None:
        self.end("a new rope", now_ns)
        here = game.location(character)
        reach = float(settings.grapple_range.value) * REACH_SLACK
        shot = aim.look(character, here, coop_code.decode_rope(code), reach)
        if shot is None:
            _say(f"co-op guest {self.name}: rope told, no surface found that way")
            return
        self.anchor = shot.anchor
        self.state = FLYING
        flight_s = shot.distance / max(1.0, float(settings.hook_speed.value))
        self.contact_ns = now_ns + int(flight_s * NS_PER_S)
        _say(f"co-op guest {self.name}: hook away, {shot.distance:.0f} away, at {shot.hit_name or 'a surface'}")
        coop_relay.guest_rope_start(self.pointer(), self.anchor, flight_s, now_ns)

    def update(self, character: Any, now_ns: int) -> None:
        movement = character.CharacterMovement
        if self.state == FLYING:
            if now_ns < self.contact_ns:
                return
            self.state = ATTACHED
            self.pull = traction.Traction(self.anchor)
            gap, tilt = self.pull.attach(character, movement, now_ns)
            _say(f"co-op guest {self.name}: hook set, pulling from {gap:.0f} away, rope {tilt:+.0f} degrees")
            return
        if self.state == ATTACHED and self.pull is not None:
            _pulled, why = self.pull.step(character, movement, now_ns, remote_stick(character), judged=False)
            if why is None and now_ns - self.pull.started_ns >= NO_WORD_S * NS_PER_S:
                why = "no word from the guest"
            if why is not None:
                self.end(why, now_ns)

    def end(self, why: str, now_ns: int) -> None:
        if self.state is None:
            return
        if self.state == ATTACHED and self.pull is not None:
            held_s = (now_ns - self.pull.started_ns) / NS_PER_S
            _say(f"co-op guest {self.name}: let go: {why}, after {held_s:.2f}s, top speed {self.pull.top_speed:.0f}, "
                 f"moved {self.pull.moved():.0f}")
        else:
            _say(f"co-op guest {self.name}: shot called off: {why}")
        self.state = None
        self.pull = None
        coop_relay.guest_rope_end(self.pointer(), now_ns)


def _rope_of(controller: Any) -> GuestRope | None:
    for rope in _ropes:
        if rope.pointer() == controller:
            return rope
    if len(_ropes) >= MAX_GUESTS:
        return None
    rope = GuestRope(controller)
    _ropes.append(rope)
    return rope


def heard(controller: Any, code: int, _now_ns: int) -> None:
    """A guest's message, kept for the next frame: the ray and the pull run with the game's frame, not inside its
    network message. Two at most, the last start and its release."""
    rope = _rope_of(controller)
    if rope is not None:
        rope.pending = (rope.pending + [code])[-2:]


def tick(now_ns: int) -> None:
    for rope in list(_ropes):
        character = rope.character()
        if character is None:
            rope.end("guest gone", now_ns)
            if rope.pointer() is None:
                _ropes.remove(rope)
            continue
        pending, rope.pending = rope.pending, []
        for code in pending:
            if code == coop_code.RELEASE:
                rope.end("released by the guest", now_ns)
            else:
                rope.start(character, code, now_ns)
        rope.update(character, now_ns)


def reset() -> None:
    """At switch-off: every guest's rope ends where it is, its speed untouched, as the player's does."""
    global _lines
    _ropes.clear()
    _lines = 0
