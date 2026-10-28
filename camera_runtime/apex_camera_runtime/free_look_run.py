"""Free Look on foot: the hunter keeps going alone in the locked direction, free of the game for its tests.

Kevin, 2026-10-07: Free Look also keeps where the hunter goes, without holding the movement key; that is what sets
it apart from the orbit camera. The speed is the one he had at the press; standing still he stays still, his body
kept in place; left and right turn the run while the camera stays free; on release he stops if no key is held.
At the wheel the vehicle only keeps its throttle until it brakes, and goes straight: the game steers vehicles with
the camera alone (Kevin, same day).
"""

import math

from .free_look_angles import turn

MOVING_SPEED = 50.0
# Starting values, tuned in the final camera session.
TURN_DEG_S = 90.0
DEAD_ZONE = 0.15
FULL_INPUT = 0.1
BRAKE_INPUT = 0.3


def clamp(value: float) -> float:
    return max(-1.0, min(1.0, float(value)))


def lateral(right: float, left: float, stick_x: float) -> float:
    """Right is positive, as the game's yaw turns."""
    return clamp(float(right) - float(left) + float(stick_x))


def braking(back: float, trigger: float) -> bool:
    return max(float(back), float(trigger)) >= BRAKE_INPUT


class Run:
    def __init__(self, yaw: float, scale: float) -> None:
        self.yaw = turn(yaw)
        self.scale = scale

    def steer(self, side: float, step_s: float) -> float:
        if abs(side) >= DEAD_ZONE:
            self.yaw = turn(self.yaw + clamp(side) * TURN_DEG_S * step_s)
        return self.yaw

    def forward(self) -> tuple:
        angle = math.radians(self.yaw)
        return math.cos(angle), math.sin(angle)


def start(speed: float, pushed: float, yaw: float) -> "Run | None":
    """None when standing still. A stick pushed halfway keeps that speed; no push (a slide) counts as full."""
    if speed < MOVING_SPEED:
        return None
    return Run(yaw, min(1.0, pushed) if pushed >= FULL_INPUT else 1.0)
