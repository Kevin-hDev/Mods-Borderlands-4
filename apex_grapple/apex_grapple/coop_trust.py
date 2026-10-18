"""Co-op host: a guest's own game keeps its place from its rope to its landing, instead of being corrected.

Corrected, a guest pulled by its own game was pulled back by the host's replay of the same rope, a little off at
every frame: the elastic Kevin felt on long ropes (11 to 28 apart in median, up to 59, measured in both copies,
docs/coop/2026-10-17-saccades-restantes.md). With the engine's two switches below on, Apex Movement's slides and climbs
stopped jolting: the host's copy of the guest followed the guest's place exactly (same document, trials 6 to 9,
verified in game). Accepted limit, as there: meanwhile an explosion on the host's side cannot push the guest.

Apex Movement turns the same switches on for its own gestures. Off is the engine's own value, so each mod puts them
back off, never as it found them: one found on, during the other mod's window, would be put back on for good.
"""

from typing import Any

from unrealsdk.unreal import WeakPointer

from . import game

SWITCHES = ("bIgnoreClientMovementErrorChecksAndCorrection", "bServerAcceptClientAuthoritativePosition")
# A guest who has not stood on the ground since its rope (a fall out of the world, a teleport in mid-air) gets the
# host's corrections back after this long. Estimate, not measured, as Apex Movement's: room for a fall and a glide.
LONGEST_NS = 10_000_000_000


def _put(movement: Any, value: bool) -> None:
    for name in SWITCHES:
        if bool(getattr(movement, name)) != value:
            setattr(movement, name, value)


class Trust:
    """One guest's window: from a rope told (`rope_on`) to the first frame on the ground after it."""

    def __init__(self) -> None:
        self.pointer: Any = None
        self.last_ns = 0

    @property
    def on(self) -> bool:
        return self.pointer is not None

    def step(self, character: Any, rope_on: bool, now_ns: int) -> str | None:
        """Holds the switches on for this frame or gives them back; says "on" or "off" on the frame it changes."""
        movement = character.CharacterMovement
        if rope_on:
            changed = None if self.on and self.pointer() == character else "on"
            if changed and self.on:
                self.give_back()
            self.pointer, self.last_ns = WeakPointer(character), now_ns
            _put(movement, True)
            return changed
        if not self.on:
            return None
        if game.is_on_ground(movement) or now_ns - self.last_ns > LONGEST_NS:
            self.give_back()
            return "off"
        _put(movement, True)
        return None

    def give_back(self) -> None:
        """Off on the character it was put on, if the game still has it, even in a vehicle; then forgotten."""
        character = self.pointer() if self.pointer is not None else None
        self.pointer = None
        if character is not None and getattr(character, "CharacterMovement", None) is not None:
            _put(character.CharacterMovement, False)
