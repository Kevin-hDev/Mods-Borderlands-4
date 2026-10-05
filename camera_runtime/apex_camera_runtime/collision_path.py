"""Resolve the swept prefix of this frame's segment without retaining world positions."""
import math
from .collision_config import (MAX_COORDINATE, MAX_DELTA, MAX_LENGTH, MIN_LENGTH,
                               RETURN_SPEED, VISIBILITY_DELAY, VISIBILITY_INWARD_SPEED)


def point(value):
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        raise ValueError("invalid collision point")
    result = tuple(float(component) for component in value)
    if not all(math.isfinite(component) and abs(component) <= MAX_COORDINATE for component in result):
        raise ValueError("invalid collision point")
    return result


def segment(anchor, desired):
    start, end = point(anchor), point(desired)
    length = math.dist(start, end)
    if not MIN_LENGTH < length <= MAX_LENGTH:
        raise ValueError("invalid collision segment")
    return start, end, length


class CollisionPath:
    def __init__(self):
        self.reset()

    def reset(self):
        self.fraction = 1.0
        self.obscured_for = 0.0
        self.initialized = False

    def resolve(self, anchor, desired, distance, delta, visible=None):
        start, end, length = segment(anchor, desired)
        if (not math.isfinite(distance) or not 0 <= distance <= length
                or not math.isfinite(delta) or delta < 0):
            raise ValueError("invalid collision clearance")
        safe = distance / length
        if visible is None and safe <= self.fraction:
            fraction = safe
        else:
            goal = safe
            if visible is not None:
                goal = min(safe, self.fraction)
                if not math.isfinite(visible) or not 0 <= visible <= distance:
                    raise ValueError("invalid visibility clearance")
                blocked = visible < distance - MIN_LENGTH
                self.obscured_for = min(VISIBILITY_DELAY, self.obscured_for + min(delta, MAX_DELTA)) if blocked else 0.0
                if blocked and self.obscured_for >= VISIBILITY_DELAY:
                    goal = visible / length
            # Visibility is comfort; physical clearance always clips the interpolated result.
            alpha = -math.expm1(-RETURN_SPEED * min(delta, MAX_DELTA))
            movement = (goal - self.fraction) * alpha
            if visible is not None:
                movement = max(movement, -VISIBILITY_INWARD_SPEED * min(delta, MAX_DELTA) / length)
            fraction = min(safe, self.fraction + movement)
            if abs(fraction - goal) * length < MIN_LENGTH:
                fraction = min(safe, goal)
        position = tuple(a + (b - a) * fraction for a, b in zip(start, end))
        self.fraction = fraction
        return position
