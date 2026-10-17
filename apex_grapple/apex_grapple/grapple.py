"""The rope's states: nothing, the hook flying, the pull, and how each pull ends.

While the hook flies the mod writes no movement: the player walks, runs, slides and jumps as
usual, while the optional visual layer follows the hand. The pull itself, its physics and its ends,
is traction.py's.

Nothing Apex Movement owns is touched by this. The mod writes a velocity, which it already did.
"""

from typing import Any

from . import (aim, coop_link, coordination, game, native_interaction, release, report, rope_effects, settings, stamina,
               traction)

IDLE = "idle"
FLYING = "flying"
ATTACHED = "attached"
NS_PER_S = 1_000_000_000

class Rope:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        """Releases the owned visuals and forgets the shot without changing momentum."""
        rope_effects.reset()
        coop_link.tell_end()
        self.state = IDLE
        self.anchor = (0.0, 0.0, 0.0)
        self._release_lets_go = True
        self._pressed_ns = 0
        self._contact_ns = 0
        self._started_ns = 0
        self._traction: traction.Traction | None = None

    @property
    def holds(self) -> bool:
        return self.state == ATTACHED

    @property
    def busy(self) -> bool:
        return self.state != IDLE

    def fire(self, character: Any, now_ns: int, native_action: bool = True, held: bool = False) -> bool:
        """Answers whether the mod takes the key. False leaves it to the game, which punches."""
        if self.busy:
            # A second press during a shot calls it off rather than stacking a second rope.
            self.let_go("cancelled", now_ns)
            return True
        native_priority = native_interaction.has_priority() if native_action else False
        if native_priority:
            return False
        for line in settings.keep_in_bounds():
            report.warning(line)
        if coordination.takeover(character) is not None:
            return False
        looking = game.aim(character)
        if looking is None:
            return False
        start, facing = looking
        shot = aim.look(character, start, facing, float(settings.grapple_range.value))
        if not aim.grapples(shot, float(settings.punch_range.value), bool(settings.melee_wins.value),
                            bool(settings.keep_game_grapple.value) and native_priority is not False,
                            keep_native_melee=native_action, explain=True):
            return False
        if not stamina.try_spend(character, float(settings.stamina_cost.value)):
            return True
        self.anchor = shot.anchor
        self.state = FLYING
        self._pressed_ns = now_ns
        # A shot fired by a hold pulls all the way: the hold was its trigger (Kevin, 2026-10-06).
        self._release_lets_go = not held
        self._started_ns = now_ns
        flight_s = shot.distance / max(1.0, float(settings.hook_speed.value))
        self._contact_ns = now_ns + int(flight_s * NS_PER_S)
        report.hook_away(shot.distance, game.pitch_of(facing), flight_s, shot.hit_name)
        rope_effects.start(character, self.anchor, now_ns, flight_s)
        coop_link.tell_start(character, self.anchor, flight_s)
        return True

    def key_up(self, now_ns: int) -> None:
        """A tap keeps its pull at any distance; releasing a held key ends an attached pull."""
        lets_go = self._release_lets_go and bool(settings.release_on_key_up.value)
        if self.holds and lets_go and release.held_key(self._pressed_ns, now_ns):
            self.let_go("key released", now_ns)

    def update(self, character: Any, now_ns: int) -> None:
        if not self.busy:
            return
        for line in settings.keep_in_bounds():
            report.warning(line)
        reason = coordination.takeover(character)
        if reason is not None:
            self.let_go(reason, now_ns)
            return
        # The hand moves during flight too; a local beam must follow before the pull attaches.
        rope_effects.follow(character, self.anchor)
        movement = character.CharacterMovement
        if self.state == FLYING:
            if now_ns < self._contact_ns:
                return
            self._attach(character, movement, now_ns)
            return
        self._pull(character, movement, now_ns)

    def _attach(self, character: Any, movement: Any, now_ns: int) -> None:
        self.state = ATTACHED
        self._started_ns = now_ns
        self._traction = traction.Traction(self.anchor)
        gap, tilt = self._traction.attach(character, movement, now_ns)
        rope_effects.hold(character, now_ns, self._traction.closest, self._traction.near(), self._traction.pull_cap)
        report.hook_set(gap, tilt)

    def _pull(self, character: Any, movement: Any, now_ns: int) -> None:
        pulled, why = self._traction.step(character, movement, now_ns, game.stick(character))
        if pulled:
            rope_effects.pulled(self._traction.to_anchor(), self._traction.velocity)
        if why is not None:
            self.let_go(why, now_ns)

    def let_go(self, why: str, now_ns: int) -> None:
        if not self.busy:
            return
        held_s = (now_ns - self._started_ns) / NS_PER_S
        if self.state == ATTACHED and self._traction is not None:
            report.note(f"let go: {why}, after {held_s:.2f}s, top speed {self._traction.top_speed:.0f}, "
                        f"moved {self._traction.moved():.0f}")
        else:
            report.note(f"shot called off: {why}")
        self.state = IDLE
        self._traction = None
        rope_effects.stop(now_ns)
        coop_link.tell_end()
