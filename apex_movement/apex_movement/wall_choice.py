"""Which surface a wall climb judges itself on, out of everything the traces met at their several heights.

Split out of climb_rules on 2026-09-18 (code review): choosing a surface is geometry, deciding a climb is a rule, and
the two sat in one file. No SDK import, so every choice is tested without the game.
"""

import math

from .climb_aim import Wall

# A face leaning more than about 45 degrees off upright is a slope to walk on, not a wall to climb.
# Its one home is here, not in climb_rules, which reads it too: the rules import this module and it never imports them,
# so both reach the threshold with no import cycle, even the day the rules pick a surface themselves.
MIN_WALL_FLAT = 0.7
# Two surfaces facing within this of each other are the same wall, seen at two heights: beyond it they are two walls,
# and averaging them would point into neither.
SAME_WALL_COS = 0.7


def best_wall(walls: list[Wall]) -> Wall | None:
    """The surface a climb should judge itself on, out of what the traces met: the nearest one upright enough to be a
    wall, or else the nearest of all, so a refusal can say how far it was and how much it leaned.

    Sorting by uprightness among those within reach cost séance U: rising past REACH left only a bevel two units away,
    the most upright of what was left at 0.53, and the climb ended on a lost wall while the panel stood at 98. Leaning
    surfaces are not candidates at all — that is what the threshold means.
    """
    if not walls:
        return None
    upright = [wall for wall in walls if wall.flat >= MIN_WALL_FLAT]
    if not upright:
        return min(walls, key=lambda wall: wall.distance)
    nearest = min(upright, key=lambda wall: wall.distance)
    # The face of a wall carries bars, bolts and corrugation. Each is upright enough to be picked on its own, and each
    # points its own way, which turns a climb or ends it (Kevin, 2026-09-17: "c'est presque plat, ça devrait être
    # considéré comme du plat"). Averaging the heights that see the same wall smooths them out.
    same = [wall for wall in upright
            if wall.into_x * nearest.into_x + wall.into_y * nearest.into_y >= SAME_WALL_COS]
    return _merged(same)


def _merged(walls: list[Wall]) -> Wall:
    """One wall out of several views of it: the nearest distance, the average way in and way up."""
    if len(walls) == 1:
        return walls[0]
    into_x, into_y = _unit(sum(w.into_x for w in walls), sum(w.into_y for w in walls))
    up_x, up_y, up_z = _unit3(sum(w.up_x for w in walls), sum(w.up_y for w in walls), sum(w.up_z for w in walls))
    return Wall(distance=min(w.distance for w in walls), into_x=into_x, into_y=into_y,
                flat=max(w.flat for w in walls), up_x=up_x, up_y=up_y, up_z=up_z)


def _unit(x: float, y: float) -> tuple[float, float]:
    length = math.hypot(x, y)
    return (x / length, y / length) if length > 1e-6 else (x, y)


def _unit3(x: float, y: float, z: float) -> tuple[float, float, float]:
    length = math.sqrt(x * x + y * y + z * z)
    return (x / length, y / length, z / length) if length > 1e-6 else (0.0, 0.0, 1.0)
