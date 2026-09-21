"""The rope's states: nothing, the hook flying, the pull, and how each pull ends.

While the hook flies the mod writes no movement: the player walks, runs, slides and jumps as
usual, while the optional visual layer follows the hand.

While the pull holds, the mod **owns** the velocity: it keeps its own, works the model on it and
writes it, without reading back what the game did to it in between. That is the difference between a
grapple and a suggestion. Apex Movement sets the air control to reach its wanted speed in a single
frame (measured 2026-09-20), so a stick pushed to the side turned the whole velocity that way before
the mod ever read it, and the pull merely added to a direction the game had already chosen — a small
hop sideways instead of a curve (Kevin: "je fais un petit saut sur la gauche").

Nothing Apex Movement owns is touched by this. The mod writes a velocity, which it already did.

The gravity of the moment is read rather than assumed, so Apex Movement's heavier fall is followed
instead of fought.

A pull ends with the speed it reached, untouched. No braking, no reset: the whole point of the Apex
grapple is the speed you leave it with.
"""

import math
from typing import Any

from . import aim, coordination, game, pull, release, report, rope_visuals, settings

IDLE = "idle"
FLYING = "flying"
ATTACHED = "attached"

# EMovementMode's Falling, from Unreal's own list (None 0, Walking 1, NavWalking 2, Falling 3).
# Velocity written while the character stands is overwritten by the game on the next frame, so a
# pull that starts on the ground has to take it off the ground first.
#
# Setting it once is not enough: the game puts a character standing on a floor straight back to
# walking. Measured on 2026-09-20, eight pulls from a standing start, all cut at 0.06 to 0.19 s by
# "landed" — the player had not left the ground yet, and the rule that ends a pull on landing read
# that first frame as an arrival. So the mode is written again on every frame of the take-off, and
# the ground does not end a pull until the take-off time is over.
MOVE_FALLING = 3
NS_PER_S = 1_000_000_000


class Rope:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        """Releases the owned visuals and forgets the shot without changing momentum."""
        rope_visuals.reset()
        self.state = IDLE
        self.anchor = (0.0, 0.0, 0.0)
        self.key_down = False
        self._pressed_ns = 0
        self._contact_ns = 0
        self._started_ns = 0
        self._last_ns = 0
        self._pull_cap = 0.0
        self._top_speed = 0.0
        self._from_spot = (0.0, 0.0, 0.0)
        self._at_spot = (0.0, 0.0, 0.0)
        self._closest = 0.0
        self._velocity = (0.0, 0.0, 0.0)

    @property
    def holds(self) -> bool:
        return self.state == ATTACHED

    @property
    def busy(self) -> bool:
        return self.state != IDLE

    def fire(self, character: Any, now_ns: int) -> bool:
        """Answers whether the mod takes the key. False leaves it to the game, which punches."""
        self.key_down = True
        if self.busy:
            # A second press during a shot calls it off rather than stacking a second rope.
            self.let_go("cancelled", now_ns)
            return True
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
                            bool(settings.keep_game_grapple.value), explain=True):
            return False
        self.anchor = shot.anchor
        self.state = FLYING
        self._pressed_ns = now_ns
        self._started_ns = now_ns
        flight_s = shot.distance / max(1.0, float(settings.hook_speed.value))
        self._contact_ns = now_ns + int(flight_s * NS_PER_S)
        report.note(f"hook away, {shot.distance:.0f} away, aim {game.pitch_of(facing):+.0f} degrees, "
                    f"flying {flight_s:.2f}s, at {shot.hit_name or 'a surface'}")
        rope_visuals.start(character, self.anchor)
        return True

    def key_up(self, now_ns: int) -> None:
        """A tap keeps its pull at any distance; releasing a held key ends an attached pull."""
        self.key_down = False
        if self.holds and bool(settings.release_on_key_up.value) and release.held_key(self._pressed_ns, now_ns):
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
        rope_visuals.follow(character, self.anchor)
        movement = character.CharacterMovement
        if self.state == FLYING:
            if now_ns < self._contact_ns:
                return
            self._attach(character, movement, now_ns)
            return
        self._pull(character, movement, now_ns)

    def _attach(self, character: Any, movement: Any, now_ns: int) -> None:
        self.state = ATTACHED
        self._started_ns = self._last_ns = now_ns
        speed = self._velocity = game.velocity(movement)
        rope = pull.toward(game.location(character), self.anchor)
        # The reading caps what the pull adds, not the total: the speed already carried along the
        # rope is kept on top of it, which is what chains one grapple into the next.
        carried = pull.speed_along(speed, rope) if rope is not None else 0.0
        self._pull_cap = carried + float(settings.pull_speed_cap.value)
        self._from_spot = self._at_spot = game.location(character)
        self._closest = math.dist(self._from_spot, self.anchor)
        rope_visuals.hold()
        if game.is_on_ground(movement):
            self._leave_ground(movement)
        # The rope's tilt says what the player really aimed at, which no other line does: a rope
        # near zero degrees drags him along the floor however high the wall looked.
        tilt = math.degrees(math.asin(max(-1.0, min(1.0, rope[2])))) if rope is not None else 0.0
        report.note(f"hook set, pulling from {math.dist(self._from_spot, self.anchor):.0f} away, "
                    f"rope {tilt:+.0f} degrees")

    def _leave_ground(self, movement: Any) -> None:
        """Puts the player in the air and gives him the speed to stay there for a moment.

        The lift is not part of the measured model: it exists only to break contact with the floor.
        Falling alone was not enough (2026-09-20, second reading): with no upward speed the game's
        own fall test finds the floor again within the same frame and walks the player, and a
        walking character has its upward speed wiped. Every pull then died at 0.36 s having moved
        one to three metres, whatever the pull had reached — up to 1850 units a second.
        """
        try:
            movement.SetMovementMode(MOVE_FALLING, 0)
        except Exception as exc:
            # The pull still writes the velocity; on the ground the game may overwrite it, which the
            # log then shows as a pull that did nothing until the player left the ground.
            report.error_once("leave_ground", f"could not take the player off the ground: {exc!r}")
            return
        lift = float(settings.takeoff_lift.value)
        if lift <= 0.0:
            return
        # Never slows a player already rising: a grapple fired out of a jump keeps its climb.
        self._velocity = (self._velocity[0], self._velocity[1], max(self._velocity[2], lift))
        game.set_velocity(movement, self._velocity)

    def _taking_off(self, now_ns: int) -> bool:
        return release.taking_off(now_ns - self._started_ns, float(settings.ground_grace.value))

    def _pull(self, character: Any, movement: Any, now_ns: int) -> None:
        step_s = (now_ns - self._last_ns) / NS_PER_S
        self._last_ns = now_ns
        if self._taking_off(now_ns) and game.is_on_ground(movement):
            # Written again rather than once: the game walks the character as soon as a floor is
            # under it, and a walking character has its velocity rewritten every frame.
            self._leave_ground(movement)
        before = self._at_spot
        here = self._at_spot = game.location(character)
        stride = math.dist(here, before)
        if release.blocked(self._velocity, stride, step_s):
            # Whatever stopped him is the game's business, and its velocity is the true one now.
            self._velocity = game.velocity(movement)
            self.let_go("hit something", now_ns)
            return
        self._velocity = pull.step(
            self._velocity, here, self.anchor, game.stick(character), game.gravity(movement),
            float(settings.pull_strength.value), self._pull_cap,
            float(settings.steer_strength.value), float(settings.steer_speed_cap.value),
            float(settings.rope_carry.value) / 100.0, step_s,
        )
        game.set_velocity(movement, self._velocity)
        self._top_speed = max(self._top_speed, math.sqrt(sum(part * part for part in self._velocity)))
        self._check_end(movement, here, stride, now_ns)

    def _check_end(self, movement: Any, here: tuple[float, float, float], stride: float, now_ns: int) -> None:
        near = release.arrival_for_shot(float(settings.arrival_distance.value),
                                        math.dist(self._from_spot, self.anchor))
        gap = math.dist(here, self.anchor)
        self._closest = min(self._closest, gap)
        if release.arrived(gap, near, stride):
            self.let_go("arrived", now_ns)
            return
        if release.passed(gap, self._closest, near):
            self.let_go("passed the anchor", now_ns)
            return
        if release.out_of_time(now_ns - self._started_ns, float(settings.longest_pull.value)):
            self.let_go("too long", now_ns)
            return
        if bool(settings.release_on_landing.value) and game.is_on_ground(movement) and not self._taking_off(now_ns):
            self.let_go("landed", now_ns)

    def let_go(self, why: str, now_ns: int) -> None:
        if not self.busy:
            return
        held_s = (now_ns - self._started_ns) / NS_PER_S
        if self.state == ATTACHED:
            report.note(f"let go: {why}, after {held_s:.2f}s, top speed {self._top_speed:.0f}, "
                        f"moved {math.dist(self._from_spot, self._at_spot):.0f}")
        else:
            report.note(f"shot called off: {why}")
        self.state = IDLE
        self._top_speed = 0.0
        rope_visuals.stop()
