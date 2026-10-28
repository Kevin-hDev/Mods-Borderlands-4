"""Validate the camera points and segments the game hands over before any sweep reads them."""
import math
from .collision_config import MAX_COORDINATE, MAX_LENGTH, MIN_LENGTH


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
