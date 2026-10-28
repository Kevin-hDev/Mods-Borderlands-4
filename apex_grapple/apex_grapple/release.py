"""When a pull ends. Numbers in, answers out: no SDK and no game object reaches this file.

Each rule here was written against a reading, and each one exists because a simpler version of it
failed in game on 2026-09-20:

- the arrival sphere has to grow with the player's stride. Pulls reached 2400 units a second, which
  at the game's frame rate is 190 units between two frames: a fixed 150 unit sphere is stepped clean
  over, and the player then swung back and forth through the anchor for three seconds.
- leaving the anchor only counts once he has been near it. A version that let go as soon as the
  distance rose cut every arc at the moment the player steered, which is the one move the mod
  exists for.
- the ground means nothing during the take-off, since a pull that starts on the player's feet has
  him standing for its first frames.
- covering far less ground than the velocity asked for means something solid is in the way. The mod
  owns the velocity during a pull, so without this it would hold a player pressed into a wall.
"""

import math

# A stride the sphere must at least cover, so that a fast player cannot step over it.
STRIDE_SHARE = 1.2
# Leave room for a real pull when the shot starts inside the configured arrival sphere.
SHORT_ARRIVAL_SHARE = 0.5
# How near the anchor he must have come for leaving it again to count as arriving.
NEAR_SHARE = 3.0
# Below this the frame moved him too little for the comparison to mean anything.
BLOCKED_FLOOR = 40.0
# Under this share of what the velocity asked for, something solid is in the way.
BLOCKED_SHARE = 0.4
NS_PER_S = 1_000_000_000
# Close hooks land before a normal tap ends; intent must use press duration, not flight time.
HOLD_PRESS_NS = 200_000_000


def held_key(pressed_ns: int, released_ns: int) -> bool:
    """Short taps keep their pull even when the hook has already landed."""
    return released_ns - pressed_ns >= HOLD_PRESS_NS


def arrival_for_shot(set_near: float, starting_gap: float) -> float:
    """Close shots travel before arriving; long shots retain the player's configured radius."""
    return min(set_near, starting_gap * SHORT_ARRIVAL_SHARE)


def arrival_radius(set_near: float, stride: float) -> float:
    """The sphere that counts as arrived this frame, never smaller than the ground covered in it."""
    return max(set_near, stride * STRIDE_SHARE)


def arrived(gap: float, set_near: float, stride: float) -> bool:
    return gap <= arrival_radius(set_near, stride)


def passed(gap: float, closest: float, set_near: float) -> bool:
    """He came near the anchor and is now leaving it: the closest point is behind him."""
    return gap > closest + set_near and closest <= set_near * NEAR_SHARE


def out_of_time(held_ns: int, longest_s: float) -> bool:
    """A limit of zero is no limit: swinging round an anchor takes far longer than flying at it."""
    return longest_s > 0.0 and held_ns >= longest_s * NS_PER_S


def blocked(velocity: tuple[float, float, float], stride: float, step_s: float) -> bool:
    """He covered far less than the velocity he was given: a wall, a ledge, something solid."""
    wanted = math.sqrt(sum(part * part for part in velocity)) * step_s
    return wanted > BLOCKED_FLOOR and stride < wanted * BLOCKED_SHARE


def taking_off(held_ns: int, grace_s: float) -> bool:
    """The opening of a pull, where the ground is still under the player's feet and means nothing."""
    return held_ns < grace_s * NS_PER_S
