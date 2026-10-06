"""Soft camera motion on foot (dynamic camera, idea 3), in the camera's axes: X forward, Y right, Z up.

The offset follows them, pitch included (Vehicle Driving's camera_geometry.py, verified in game).
- Inertia: the camera reacts late to a change of speed (a start, a stop, a turn, a jump, a landing) and comes back.
  It follows the change, not the speed: a lag on the speed itself would keep the hunter off-centre through a whole
  strafe or sprint.
- Idle: after a second standing still, a slow faint drift, like a camera held by hand.
These are the trial's values: Kevin, 2026-10-06, « on sent légèrement le mouvement sans que ce soit trop, on va
garder ça ». The strength setting scales them. No lag on the camera's turning: it would fight aiming with a mouse.
"""

import math

from .easing import MAX_STEP_S, Easing
from .player_sample import Sample

# Seconds of lag per unit of speed change: Apex Movement's instant 801 at a sprint's start gives about 32.
INERTIA_S = 0.04
INERTIA_UP_S = 0.03
# Limits per axis (forward, right, up), so a dash or a fall never throws the camera far.
LIMITS = (40.0, 35.0, 30.0)
# How long the camera takes to catch up with a change of speed (95 %).
CATCH_UP_SECONDS = 0.45
# The output is eased too: the speed jumps in one frame at a sprint's start, the camera must not.
OUTPUT_SECONDS = 0.25
AIM_SECONDS = 0.15
IDLE_AFTER_S = 1.0
IDLE_SPEED = 20.0
IDLE_SECONDS = 1.5
# Right and up amplitudes; periods with no common beat, so the drift never looks like a loop.
IDLE_AMPLITUDE = (3.0, 2.0)
IDLE_PERIODS = (5.3, 3.7)
REST = 0.01
ZERO = (0.0, 0.0, 0.0)


def to_camera(world: tuple, pitch: float, yaw: float) -> tuple[float, float, float]:
    p, y = math.radians(pitch), math.radians(yaw)
    sp, cp, sy, cy = math.sin(p), math.cos(p), math.sin(y), math.cos(y)
    axes = ((cp * cy, cp * sy, sp), (-sy, cy, 0.0), (-sp * cy, -sp * sy, cp))
    return tuple(sum(w * a for w, a in zip(world, axis)) for axis in axes)


def clamp(values: tuple) -> tuple:
    return tuple(max(-limit, min(limit, value)) for value, limit in zip(values, LIMITS))


class Motion:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.followed = Easing(3, REST)
        self.output = Easing(3, REST)
        self.idle = Easing(1, REST)
        self.primed = False
        self.still_s = 0.0
        self.clock = 0.0

    def step(self, strength: float, sample: Sample | None, pitch: float, yaw: float, step_s: float) -> tuple:
        step_s = min(max(step_s, 0.0), MAX_STEP_S)
        self.clock += step_s
        if strength <= 0 or sample is None or sample.aiming:
            self.primed = False
            self.still_s = 0.0
            self.idle.reset()
            return self.output.step(ZERO, AIM_SECONDS, step_s)
        if not self.primed:
            # Started or back after a pause: the speed it finds is not a change.
            self.followed.snap(sample.velocity)
            self.primed = True
        caught = self.followed.step(sample.velocity, CATCH_UP_SECONDS, step_s)
        lag = tuple((caught[axis] - sample.velocity[axis]) * (INERTIA_UP_S if axis == 2 else INERTIA_S)
                    for axis in range(3))
        inertia = clamp(to_camera(lag, pitch, yaw))
        self.still_s = self.still_s + step_s if sample.flat_speed < IDLE_SPEED and not sample.in_air else 0.0
        weight = self.idle.step((1.0 if self.still_s >= IDLE_AFTER_S else 0.0,), IDLE_SECONDS, step_s)[0]
        drift = tuple(weight * amplitude * math.sin(2 * math.pi * self.clock / period + phase)
                      for amplitude, period, phase in zip(IDLE_AMPLITUDE, IDLE_PERIODS, (0.0, 1.0)))
        goal = (inertia[0] * strength, (inertia[1] + drift[0]) * strength, (inertia[2] + drift[1]) * strength)
        return self.output.step(goal, OUTPUT_SECONDS, step_s)
