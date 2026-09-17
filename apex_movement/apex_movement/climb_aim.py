"""Aiming a wall climb: the wall the trace found, the angles to it, and the direction a climb goes in.

Split out of climb_rules on 2026-09-17, when refusals had to be told apart in the log: the rules grew a reason for
every way a climb can fail to start, and the geometry they lean on belongs to itself. No SDK import, so every angle is
tested without the game.

A Wall is whatever the trace touched, floor or ceiling included: how upright it stands is `flat`, and deciding what is
climbable is a rule, not a measure (climb_rules). Before that, wall_sense threw a slope away and the log could not say
a climb was refused because the surface leaned.
"""

import math
from dataclasses import dataclass

# What a surface's normal keeps flat when it stands straight up: 1 a vertical wall, 0 a floor or a ceiling.
FLAT_UPRIGHT = 1.0
# Where a climb looks for its wall, in shares of the character's half height from its centre: from just under the feet
# to over the head. One height alone slipped through the gaps of an uneven face (Kevin, séance O), and three starting
# at -0.7 still missed what blocked the player: the probe's profile found an upright face right at the feet, at -1.2,
# on all three zones that refused to be climbed (séance R). The log counts how many of these met anything, so "no wall"
# tells a structure the traces go through from a wall the rules turned down.
TRACE_HEIGHTS = (-1.2, -0.6, 0.0, 0.6, 1.2)
# From this height up, a hit means a wall the character's own body would meet, not a step it can be lifted over.
HIGH_FROM = 0.0


@dataclass(frozen=True)
class Wall:
    distance: float
    # The way into the wall, flat and one unit long; both zero when the surface faces straight up or down.
    into_x: float
    into_y: float
    # How much of the surface's normal is horizontal: FLAT_UPRIGHT for a wall standing straight, 0 for a floor.
    flat: float
    # The way up along the surface, one unit long. Straight up by default, which is what a wall standing straight
    # gives: a leaning wall tips it into itself, so climbing follows the face instead of drifting away from it.
    up_x: float = 0.0
    up_y: float = 0.0
    up_z: float = 1.0


def angle_to_wall(x: float, y: float, wall: Wall) -> float:
    """Degrees between a flat direction and the way into the wall; no direction at all counts as turned away."""
    length = math.hypot(x, y)
    if length < 1e-6:
        return 180.0
    cosine = (x * wall.into_x + y * wall.into_y) / length
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def view_angle(yaw: float | None, wall: Wall) -> float:
    if yaw is None:
        return 180.0
    angle = math.radians(yaw)
    return angle_to_wall(math.cos(angle), math.sin(angle), wall)


def lean_degrees(x: float, y: float, wall: Wall, limit_deg: float) -> float:
    """How far the stick leans along the wall: 0 straight up, negative on one side and positive on the other.

    Bounded by the limit, so that between it and the end angle a climb keeps its fullest diagonal instead of ending.
    """
    if math.hypot(x, y) < 1e-6:
        return 0.0
    along = x * -wall.into_y + y * wall.into_x
    into = x * wall.into_x + y * wall.into_y
    return max(-limit_deg, min(limit_deg, math.degrees(math.atan2(along, into))))


def climb_direction(lean_deg: float, wall: Wall) -> tuple[float, float, float]:
    """A unit direction to climb in: up along the wall's own face, tipped by lean_deg to one side of it.

    Following the face matters on a wall that leans back: séance U measured one at 72 degrees, where climbing straight
    up moved the character 30 further from it every 100 risen, until the wall was out of reach and the climb died.
    """
    lean = math.radians(lean_deg)
    rise, sideways = math.cos(lean), math.sin(lean)
    return (wall.up_x * rise - wall.into_y * sideways,
            wall.up_y * rise + wall.into_x * sideways,
            wall.up_z * rise)


def longest_climb_s(height: float, speed: float, lean_deg: float) -> float:
    """The longest a climb can last: leaning all the way rises the slowest, so it takes the longest to reach height."""
    return height / (speed * math.cos(math.radians(lean_deg)))
