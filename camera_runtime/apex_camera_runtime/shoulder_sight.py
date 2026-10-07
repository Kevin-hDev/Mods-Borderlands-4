"""How far each shoulder's camera sees ahead before a wall (first trial, Kevin, 2026-10-07).

A wall in front of the shoulder hides the view without touching the camera: on Kevin's screenshots the wall filled the
right half of the screen and the reticle sat on it, while the wall check counted the camera clear. So each side also
looks straight ahead, level, from its camera: a level line ignores the floor when the player looks down.
"""

import math

from .shoulder_auto import BLOCKED, CLEAR

# Distances from the camera (cm), which sits about 2.6 m behind the hunter (dynamic camera trial, 2026-10-06).
# A wall nearer than BLOCKED_CM is in the way: about 2.5 m ahead of the hunter (Kevin, 2026-10-07 second trial: at
# 1.4 m the swap came late). The other side must see past CLEAR_CM to be worth going to; the view counts fully clear
# past SIGHT_CM.
BLOCKED_CM = 510.0
CLEAR_CM = 720.0
SIGHT_CM = 800.0
# Distance to free share, matched to shoulder_auto.py's thresholds: BLOCKED_CM gives BLOCKED, CLEAR_CM gives CLEAR.
SCALE = ((0.0, 0.0), (BLOCKED_CM, BLOCKED), (CLEAR_CM, CLEAR), (SIGHT_CM, 1.0))
RADIUS = 5.0
# TraceTypeQuery2, the engine's Camera channel: characters ignore it, so an enemy ahead is not a wall.
CAMERA_CHANNEL = 2


def free_share(distance: float) -> float:
    for (near, low), (far, high) in zip(SCALE, SCALE[1:]):
        if distance <= far:
            return low + (high - low) * (distance - near) / (far - near)
    return 1.0


class ShoulderSight:
    def __init__(self, kismet, sdk) -> None:
        self.kismet, self.sdk = kismet, sdk

    def share(self, actor, start, yaw: float) -> float:
        """Free share of the view ahead of start (free_share), level, along the camera's yaw (degrees)."""
        angle = math.radians(yaw)
        end = (start[0] + math.cos(angle) * SIGHT_CM, start[1] + math.sin(angle) * SIGHT_CM, start[2])
        first = self.sdk.make_struct("Vector", X=start[0], Y=start[1], Z=start[2])
        last = self.sdk.make_struct("Vector", X=end[0], Y=end[1], Z=end[2])
        nearest = SIGHT_CM
        for detailed in (False, True):
            answer = self.kismet.SphereTraceSingle(
                actor, first, last, RADIUS, CAMERA_CHANNEL, detailed, [actor], 0,
                self.sdk.make_struct("HitResult"), True, self.sdk.make_struct("LinearColor"),
                self.sdk.make_struct("LinearColor"), 0.0)
            if not isinstance(answer, tuple) or not 2 <= len(answer) <= 3 or type(answer[0]) is not bool:
                raise ValueError("invalid sight result")
            if answer[0]:
                distance = float(answer[-1].Distance)
                if not math.isfinite(distance) or not 0 <= distance <= SIGHT_CM:
                    raise ValueError("invalid sight contact")
                nearest = min(nearest, distance)
        return free_share(nearest)
