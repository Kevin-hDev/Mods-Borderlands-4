"""The jump budget of a wall climb: a climb gives both jumps back, like a landing, and every jump in the air is written down.

Kevin, 2026-09-17: "à partir du moment où on grimpe, ça reset les deux sauts, qu'on puisse refaire les deux sauts à
chaque fois, le même principe qu'au sol, comme si le mod considérait qu'une grimpe était une chute qui touche le sol".
The game counts two jumps (JumpMaxCount 2) and only a landing puts the count back. So a climb puts it back to one jump
used, and then gives one jump back again the next time a jump is spent in the air: the player jumps from the wall, or
in the fall, and still has the double jump. The next climb starts the same budget over.

Each gift waits for Croix to be released: the count given back on the frame of the jump, while a press the game still
sees lasts 88 to 96 ms (session E), was spent again at once, which made the double jump come and go (session K).
"""

from typing import Any, Callable

from . import game

# What a climb leaves counted: one jump, as after a jump from the ground, so a jump is always available on the wall.
KEPT_JUMPS = 1
# A player holding Croix keeps the count as it is; past this the gift is dropped rather than kept forever.
GIVE_BACK_MAX_NS = 2_000_000_000


class JumpBudget:
    """One character's jump budget. A class since 2026-10-17: a co-op host keeps one for each guest who climbs, the
    host's game counting the guest's jumps on its own (docs/coop/2026-10-17-grimpe-invite.md)."""

    def __init__(self, say: Callable[[str], None]) -> None:
        self.say = say
        self.reset()

    def reset(self) -> None:
        self.wanted: int | None = None
        self.why = ""
        self.asked_ns = 0
        # Jumps the climb still owes back: one, so that the climb's two jumps are the player's jump and the double jump.
        self.owed = 0
        self.seen: tuple[int, str] | None = None

    def climb_started(self, character: Any, now_ns: int) -> None:
        """A climb counts as a landing: one jump used at most, and one more given back when the next one is spent."""
        self.owed = 1
        if game.jump_count(character) > KEPT_JUMPS:
            self._want(KEPT_JUMPS, now_ns, "wall climb: both jumps are back")

    def update(self, character: Any, now_ns: int) -> int | None:
        """Watches the jumps, gives one back after a jump in the air, and writes the count once Croix is released."""
        spent = self._watch(character)
        if spent and self.owed > 0:
            self.owed -= 1
            self._want(game.jump_count(character) - 1, now_ns, "jump from the climb: the next jump is back")
        if self.wanted is None:
            return None
        if bool(character.bPressedJump):
            if now_ns - self.asked_ns > GIVE_BACK_MAX_NS:
                self.wanted = None
                self.say(f"{self.why}: not given back, Croix still held")
            return None
        given, count = self.wanted, game.jump_count(character)
        self.wanted = None
        if count > given:
            game.set_jump_count(character, given)
            # The watch follows the count the mod wrote, so that the player's next jump still reads as one.
            self.seen = (given, self.seen[1]) if self.seen is not None else None
            self.say(f"{self.why}: jump count {count} -> {given}")
        return given

    def _want(self, count: int, now_ns: int, why: str) -> None:
        self.wanted, self.why, self.asked_ns = count, why, now_ns

    def _watch(self, character: Any) -> bool:
        """True when a jump was just spent in the air; one line per change of the count or of the jump type."""
        movement = character.CharacterMovement
        if not game.is_in_air(movement):
            # The game puts the count back itself at a landing, and the climb owes nothing any more.
            self.seen, self.owed = None, 0
            return False
        now = (game.jump_count(character), game.jump_type(movement))
        if now == self.seen:
            return False
        was, self.seen = self.seen, now
        if was is None:
            return False
        self.say(f"air jump count={now[0]} type={now[1]} croix={'held' if character.bPressedJump else 'free'}")
        return now[0] > was[0]
