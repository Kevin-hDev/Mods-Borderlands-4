"""The speed an Apex-style slide should have, frame by frame, for one character.

Split from slide_physics.py on 2026-10-16 so that a co-op host can run one model per guest: the host computes every
guest's slide itself, and must slow it down exactly as the guest's own game does, or it pulls the guest forward
(docs/coop/2026-10-16-essai-recopie-dans-apex.md). Nothing here writes into the game.

A slide's distance is (start speed squared - stop speed squared) / (2 x slowdown), so starting faster already goes
further by that ratio of squares; an Axle slide's slowdown is scaled by that ratio over the distance wanted.
"""

import math
from typing import Any

from . import axle_slide, game

# The game's own slides ended at 316 to 568 (2026-09-17, 02:05): below this a slide has run out of speed.
STOP_SPEED = 350.0
# A frame longer than this, such as a hitch while loading, is counted as this long.
MAX_STEP_S = 0.1


def friction(start_speed: float, distance: float) -> float:
    """The steady slowdown that takes a slide from its start speed to STOP_SPEED over the distance on flat ground."""
    return max((start_speed ** 2 - STOP_SPEED ** 2) / (2.0 * max(distance, 1.0)), 1.0)


def downhill(normal: Any, velocity: Any) -> float:
    """Slope along the slide, positive going down: a floor that falls away ahead tilts its normal forward."""
    speed = math.hypot(velocity.X, velocity.Y)
    if speed < 1.0:
        return 0.0
    return (normal.X * velocity.X + normal.Y * velocity.Y) / speed


def next_speed(speed: float, step_s: float, slope: float, slowdown: float, pull: float, top: float,
               scale: float = 1.0) -> float:
    return min(max(speed + scale * (pull * slope - slowdown) * step_s, 0.0), top)


def speed_gain(normal_start: float, boost: axle_slide.Boost) -> float:
    """How many times further a slide goes for starting at the boosted speed, slowing down as a normal slide."""
    boosted = normal_start * boost.speed
    return max(boosted ** 2 - STOP_SPEED ** 2, 1.0) / max(normal_start ** 2 - STOP_SPEED ** 2, 1.0)


class Model:
    """One slide of one character, from the frame it is first seen sliding."""

    def __init__(self, now_ns: int, normal_start: float, boost: axle_slide.Boost, flat_distance: float) -> None:
        self.start_ns = self.last_ns = now_ns
        # Read once: an Axle slide switched on or off mid-slide keeps the boost it started with, like its start speed.
        self.boost = boost
        self.speed = self.top = normal_start * boost.speed
        self.gain = speed_gain(normal_start, boost)
        self.slowdown = friction(normal_start, flat_distance)
        self.slope_sum = 0.0
        self.ground_frames = 0
        self.ratio_sum = 0.0
        self.ratio_frames = 0
        self.ended = False

    def step(self, movement: Any, now_ns: int, pull: float, top: float) -> float:
        """Advances the model to this frame and gives the speed the slide should have now."""
        step_s = min((now_ns - self.last_ns) / 1e9, MAX_STEP_S)
        self.last_ns = now_ns
        # In the air, off a ramp, the game keeps the slide going: nothing rubs and no slope pulls.
        if not game.is_on_ground(movement):
            return self.speed
        if self.ground_frames > 0 and not self.ended:
            # The game's speed this frame came from last frame's write: compared with the model speed written then.
            self.ratio_sum += game.horizontal_speed(movement) / max(self.speed, 1.0)
            self.ratio_frames += 1
        slope = downhill(movement.CurrentFloor.HitResult.ImpactNormal, movement.Velocity)
        self.slope_sum += slope
        self.ground_frames += 1
        self.speed = next_speed(self.speed, step_s, slope, self.slowdown, pull, top * self.boost.speed,
                                self.gain / axle_slide.distance(self.boost, slope))
        self.top = max(self.top, self.speed)
        return self.speed

    def out_of_speed(self) -> bool:
        return self.speed <= STOP_SPEED
