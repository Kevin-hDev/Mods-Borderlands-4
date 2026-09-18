"""Tells why a climb did not start, one line per time in the air.

Kevin, 2026-09-17: on some structures a climb starts on one part of a wall and not on another. The log said nothing at
all about it — a climb that never starts wrote no line — so twelve tries left four lines, all of them successes.

The reason written is the furthest one reached during the flight, not the first: every jump begins far from any wall,
so the first reason is always "no wall" and says nothing. It is written when the player lands, with the measures of
the moment it was reached, so one line answers "how close did I get, and what stopped it".

A frame where the stick asks for nothing never beats one where it does, however far down the list it got. In séance P
that rule was missing and it cost the séance: the player let the stick go at the end of a flight, a metre from a wall,
and the line read "no stick" — hiding every frame of the real try.
"""

import math
from typing import Any

from . import climb_aim, climb_rules, report, wall_choice

# The rules own the list, so a reason added there is told here without anything else to remember.
ORDER = climb_rules.REFUSALS

_best = (0, -1)
_seen: tuple[str, Any, Any] | None = None


def note(refusal: str, moment: climb_rules.Moment, limits: climb_rules.Limits) -> None:
    """Follows one frame that started no climb; landing writes the flight's furthest reason."""
    global _best, _seen
    if refusal == climb_rules.ON_GROUND:
        _tell()
        return
    asked = math.hypot(moment.stick_x, moment.stick_y) >= climb_rules.MIN_STICK
    rank = (1 if asked else 0, ORDER.index(refusal) if refusal in ORDER else -1)
    if rank > _best:
        _best, _seen = rank, (refusal, moment, limits)


def started() -> None:
    """A climb started: the flight that led to it has nothing to explain."""
    reset()


def reset() -> None:
    global _best, _seen
    _best, _seen = (0, -1), None


def _tell() -> None:
    if _seen is None:
        return
    refusal, moment, limits = _seen
    reset()
    report.note(f"wall climb refused reason={refusal} {_measures(moment, limits)}")


def _measures(moment: climb_rules.Moment, limits: climb_rules.Limits) -> str:
    stick = (f"hits={moment.hits}/{len(climb_aim.TRACE_HEIGHTS)} "
             f"stick={math.hypot(moment.stick_x, moment.stick_y):.2f}")
    wall = moment.wall
    if wall is None:
        return f"wall=none {stick}"
    return (f"distance={wall.distance:.0f} flat={wall.flat:.2f} {stick} "
            f"stick_deg={climb_aim.angle_to_wall(moment.stick_x, moment.stick_y, wall):.0f} "
            f"view_deg={climb_aim.view_angle(moment.view_yaw, wall):.0f} "
            f"needs distance<={climb_rules.REACH:.0f} flat>={wall_choice.MIN_WALL_FLAT:.2f} "
            f"stick_deg<={climb_rules.start_angle(limits):.0f} view_deg<={climb_rules.view_angle_allowed(limits):.0f}")
