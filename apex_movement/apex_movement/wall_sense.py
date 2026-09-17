"""Feels the wall in front of the player for the wall climb: three traces along the camera, at three heights.

Recipe verified in game (question 1, 2026-09-16): KismetSystemLibrary.LineTraceSingle called on the class default
object, the character as world context, every output and drawing parameter passed. On 2026-09-17 (M4) the same trace
met walls, crates and the game's invisible blocking volumes, and not a friendly character two steps away — but on the
visibility channel, which several scrap walls ignore entirely.

One trace at the centre was not enough (Kevin, 2026-09-17, séance O): at the foot of a sheet-metal structure seven
tries in a row reported no wall at all, and three climbs that did start lost the wall after rising 11, 23 and 51. A
single line at one height slips through the gaps of an uneven face. Three traces, at the feet, the centre and the head,
cover the character's own height instead.

The range is far longer than a climb needs: the rules turn a wall down past REACH anyway, and a trace that reaches
further turns "nothing in front" into "a wall, this far", which is the difference between a log that explains a refusal
and one that does not.

Whatever the traces touch comes back, slopes and floors included: how upright a surface stands is measured here and
judged in climb_rules, so a refused climb can say the surface leaned instead of saying nothing at all.
"""

import math
from typing import Any

import unrealsdk

from .climb_aim import TRACE_HEIGHTS, Wall

TRACE_RANGE = 300.0
# The traces start this far behind the character. A climb leans into its wall, and once the capsule touches it the
# centre can sit inside the surface: a ray starting there meets nothing, since a face is invisible from behind. That
# killed 13 climbs out of 42 within one or two frames in séance Z, each ending as a lost wall after rising 7 to 15.
# Backing the start off puts it outside the wall again; the distance reported takes the offset back out.
BACK_OFF = 60.0
# Channel 2, not the visibility channel 0 the mod used until 0.9.5. Measured on 2026-09-17 (séance T,
# apex_probe_ways): on six walls, channel 2 met the panel every time, from 28 to 76 away and 72 to 90 degrees upright,
# while channel 0 met nothing at all on three of them and, on a fourth, the slope 259 behind the wall. These panels
# block the player but ignore visibility, so a ray on channel 0 goes straight through them.
TRACE_CHANNEL = 2

_library: Any = None


def reset() -> None:
    global _library
    _library = None


def _kismet() -> Any:
    global _library
    if _library is None:
        _library = unrealsdk.find_class("KismetSystemLibrary").ClassDefaultObject
    return _library


_heights: list[float] = []


def walls_ahead(character: Any, yaw: float, half_height: float) -> list[Wall]:
    """Every surface the traces met, lowest height first; an empty list when they all went through."""
    centre = character.K2_GetActorLocation()
    angle = math.radians(yaw)
    ahead_x, ahead_y = math.cos(angle), math.sin(angle)
    reach_x, reach_y = ahead_x * (TRACE_RANGE + BACK_OFF), ahead_y * (TRACE_RANGE + BACK_OFF)
    back_x, back_y = centre.X - ahead_x * BACK_OFF, centre.Y - ahead_y * BACK_OFF
    found: list[Wall] = []
    _heights.clear()
    for share in TRACE_HEIGHTS:
        z = centre.Z + share * half_height
        wall = _trace(character, back_x, back_y, z, reach_x, reach_y)
        if wall is not None:
            found.append(wall)
            _heights.append(share)
    return found


def hit_heights(walls: list[Wall]) -> list[float]:
    """The height each of the last walls_ahead surfaces was met at, in the same order."""
    return list(_heights) if len(_heights) == len(walls) else [TRACE_HEIGHTS[0]] * len(walls)


def _trace(character: Any, x: float, y: float, z: float, reach_x: float, reach_y: float) -> Wall | None:
    start = unrealsdk.make_struct("Vector", X=x, Y=y, Z=z)
    end = unrealsdk.make_struct("Vector", X=x + reach_x, Y=y + reach_y, Z=z)
    hit, _ignored, result = _kismet().LineTraceSingle(
        character, start, end, TRACE_CHANNEL, False, [], 0, unrealsdk.make_struct("HitResult"), True,
        unrealsdk.make_struct("LinearColor"), unrealsdk.make_struct("LinearColor"), 0.0,
    )
    if not hit:
        return None
    normal_x, normal_y, normal_z = float(result.Normal.X), float(result.Normal.Y), float(result.Normal.Z)
    flat = math.hypot(normal_x, normal_y)
    # From the character's own centre, which is what every rule is written against.
    distance = max(0.0, float(result.Distance) - BACK_OFF)
    if flat < 1e-6:
        # A surface facing straight up or down has no way into it; the rules turn it down on its flatness.
        return Wall(distance=distance, into_x=0.0, into_y=0.0, flat=flat)
    up_x, up_y, up_z = _up_along(normal_x, normal_y, normal_z)
    return Wall(distance=distance, into_x=-normal_x / flat, into_y=-normal_y / flat, flat=flat,
                up_x=up_x, up_y=up_y, up_z=up_z)


def _up_along(normal_x: float, normal_y: float, normal_z: float) -> tuple[float, float, float]:
    """The way up along the surface: straight up with the part that leaves the surface taken out of it."""
    along = (-normal_z * normal_x, -normal_z * normal_y, 1.0 - normal_z * normal_z)
    length = math.sqrt(sum(part * part for part in along))
    if length < 1e-6:
        return 0.0, 0.0, 1.0
    return along[0] / length, along[1] / length, along[2] / length
