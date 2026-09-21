"""Local beam geometry: move its origin to the hand and aim its X axis at the anchor.

Trial A, 2026-09-21: recovered native stores contain Source=0 and Target=(length,0,0).
Emitter internals remain unreadable; only Kevin's next session can confirm this interpretation.
"""

import math
from typing import Any

import unrealsdk

from . import rope_ends

ORIGIN = (0.0, 0.0, 0.0)
MAX_COORDINATE = 1_000_000_000.0


def facing(hand: tuple, anchor: tuple) -> tuple[float, float]:
    """Pitch and yaw of local X in Unreal's world axes."""
    for spot in (hand, anchor):
        if len(spot) != 3 or any(not math.isfinite(v) or abs(v) > MAX_COORDINATE for v in spot):
            raise ValueError("invalid rope coordinates")
    east, north, up = (anchor[axis] - hand[axis] for axis in range(3))
    return math.degrees(math.atan2(up, math.hypot(east, north))), math.degrees(math.atan2(north, east))


def follow(component: Any, hand: tuple, anchor: tuple) -> tuple[float, float, float]:
    """Raises to beam's visual-only guard; never changes the character or its movement.

    Signature: Epic UE 5.5 SceneComponent API, consulted 2026-09-21; BL4 call still needs testing.
    The SDK returns (Ellipsis, SweepHitResult). No output is needed, so the tuple is discarded.
    """
    pitch, yaw = facing(hand, anchor)
    length = math.dist(hand, anchor)
    component.K2_SetWorldLocationAndRotation(
        rope_ends.vector(hand), unrealsdk.make_struct("Rotator", Pitch=pitch, Yaw=yaw, Roll=0.0),
        False, unrealsdk.make_struct("HitResult"), True,
    )
    return length, 0.0, 0.0
