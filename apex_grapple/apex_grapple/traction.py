"""One pull, from the moment the hook bites to the moment it lets go: the one place the pull's physics live.

Shared by the player's own rope (grapple.py) and by the rope a co-op host plays for each guest (coop_host.py): both
must pull the same way, or the host would carry the guest elsewhere than the guest's own game does, and correct it.

While the pull holds, it **owns** the velocity: it keeps its own, works the model on it and writes it, without reading
back what the game did to it in between. That is the difference between a grapple and a suggestion. Apex Movement sets
the air control to reach its wanted speed in a single frame (measured 2026-09-20), so a stick pushed to the side turned
the whole velocity that way before the mod ever read it, and the pull merely added to a direction the game had already
chosen — a small hop sideways instead of a curve (Kevin: "je fais un petit saut sur la gauche").

The gravity of the moment is read rather than assumed, so Apex Movement's heavier fall is followed instead of fought.

A pull ends with the speed it reached, untouched. No braking, no reset: the whole point of the Apex grapple is the
speed you leave it with.
"""

import math
from typing import Any

from . import game, pull, release, report, settings

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


class Traction:
    def __init__(self, anchor: tuple[float, float, float]) -> None:
        self.anchor = anchor
        self.started_ns = 0
        self._last_ns = 0
        self.pull_cap = 0.0
        self.top_speed = 0.0
        self.from_spot = (0.0, 0.0, 0.0)
        self.at_spot = (0.0, 0.0, 0.0)
        self.closest = 0.0
        self.velocity = (0.0, 0.0, 0.0)

    def attach(self, character: Any, movement: Any, now_ns: int) -> tuple[float, float]:
        """The hook bites: takes the character off the ground if needed. Answers the gap to the anchor and the rope's
        tilt in degrees."""
        self.started_ns = self._last_ns = now_ns
        speed = self.velocity = game.velocity(movement)
        rope = pull.toward(game.location(character), self.anchor)
        # The reading caps what the pull adds, not the total: the speed already carried along the
        # rope is kept on top of it, which is what chains one grapple into the next.
        carried = pull.speed_along(speed, rope) if rope is not None else 0.0
        self.pull_cap = carried + float(settings.pull_speed_cap.value)
        self.from_spot = self.at_spot = game.location(character)
        self.closest = math.dist(self.from_spot, self.anchor)
        if game.is_on_ground(movement):
            self._leave_ground(movement)
        # The rope's tilt says what the player really aimed at, which no other line does: a rope
        # near zero degrees drags him along the floor however high the wall looked.
        tilt = math.degrees(math.asin(max(-1.0, min(1.0, rope[2])))) if rope is not None else 0.0
        return math.dist(self.from_spot, self.anchor), tilt

    def _leave_ground(self, movement: Any) -> None:
        """Puts the character in the air and gives it the speed to stay there for a moment.

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
        self.velocity = (self.velocity[0], self.velocity[1], max(self.velocity[2], lift))
        game.set_velocity(movement, self.velocity)

    def _taking_off(self, now_ns: int) -> bool:
        return release.taking_off(now_ns - self.started_ns, float(settings.ground_grace.value))

    def near(self) -> float:
        """How near the anchor this pull lets go."""
        return release.arrival_for_shot(float(settings.arrival_distance.value), math.dist(self.from_spot, self.anchor))

    def moved(self) -> float:
        return math.dist(self.from_spot, self.at_spot)

    def to_anchor(self) -> tuple[float, float, float]:
        return tuple(a - h for a, h in zip(self.anchor, self.at_spot))

    def step(self, character: Any, movement: Any, now_ns: int, stick: tuple[float, float, float],
             judged: bool = True) -> tuple[bool, str | None]:
        """One frame of the pull: whether it wrote a velocity, and why it ends, None while it holds.

        `judged` False leaves the ends to someone else but the longest pull: a co-op host's copy of a guest moves only
        when the guest's moves arrive, not at every frame, so its strides read as walls (verified in the logs,
        docs/coop/2026-10-17-grappin-invite.md, trial 4)."""
        step_s = (now_ns - self._last_ns) / NS_PER_S
        self._last_ns = now_ns
        if self._taking_off(now_ns) and game.is_on_ground(movement):
            # Written again rather than once: the game walks the character as soon as a floor is
            # under it, and a walking character has its velocity rewritten every frame.
            self._leave_ground(movement)
        before = self.at_spot
        here = self.at_spot = game.location(character)
        stride = math.dist(here, before)
        if judged and release.blocked(self.velocity, stride, step_s):
            # Whatever stopped it is the game's business, and its velocity is the true one now.
            self.velocity = game.velocity(movement)
            return False, "hit something"
        self.velocity = pull.step(
            self.velocity, here, self.anchor, stick, game.gravity(movement),
            float(settings.pull_strength.value), self.pull_cap,
            float(settings.steer_strength.value), float(settings.steer_speed_cap.value),
            float(settings.rope_carry.value) / 100.0, step_s,
        )
        game.set_velocity(movement, self.velocity)
        self.top_speed = max(self.top_speed, math.sqrt(sum(part * part for part in self.velocity)))
        if not judged:
            return True, "too long" if self._too_long(now_ns) else None
        return True, self._end(movement, here, stride, now_ns)

    def _too_long(self, now_ns: int) -> bool:
        return release.out_of_time(now_ns - self.started_ns, float(settings.longest_pull.value))

    def _end(self, movement: Any, here: tuple[float, float, float], stride: float, now_ns: int) -> str | None:
        near = self.near()
        gap = math.dist(here, self.anchor)
        self.closest = min(self.closest, gap)
        if release.arrived(gap, near, stride):
            return "arrived"
        if release.passed(gap, self.closest, near):
            return "passed the anchor"
        if self._too_long(now_ns):
            return "too long"
        if bool(settings.release_on_landing.value) and game.is_on_ground(movement) and not self._taking_off(now_ns):
            return "landed"
        return None
