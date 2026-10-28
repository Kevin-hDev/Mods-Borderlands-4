"""Measured Orbit distance and the player-approved zoom step."""

import math

MIN_DISTANCE = 75
MAX_DISTANCE = 600
NATIVE_DISTANCE = 300
DISTANCE_STEP = 25
OFFSET_TOLERANCE = 0.001
FRAME = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"


def valid_distance(value: object) -> bool:
    return (type(value) in (int, float) and math.isfinite(value)
            and MIN_DISTANCE <= value <= MAX_DISTANCE)
