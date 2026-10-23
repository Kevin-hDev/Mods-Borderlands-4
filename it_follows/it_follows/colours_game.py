"""The game's side of the saturated colours (colours.py): the post processes of the world that set the saturation,
found, read and written.

Trial 117 (vérifié en jeu): the time of day's PostProcessComponent (WorldTimeOfDayActor), unbound, priority 88, sets
ColorSaturation for the whole world; some level volumes (PostProcessVolume), priority 900, set it within their bounds.
Trial 118: written in place through the struct the SDK gives, it holds, and the picture takes it, in first and third
person (Kevin). Found with the game's own search (reads.search): 0.03 to 0.06 ms a class in trial 38, where find_all
took 9 to 13 ms; without it nothing is found, rather than hold an image that long each second.
"""

from itertools import islice
import math
from typing import Any

import unrealsdk

from .characters import reads

TIME_OF_DAY = "WorldTimeOfDayActor"
VOLUME = "PostProcessVolume"
MAX_FOUND = 64
# The engine's saturation is a factor; the photo mode's slider goes up to 2.
SMALLEST, LARGEST = 0.0, 4.0
TOLERANCE = 1e-3


class SearchUnavailable(Exception):
    """The game's search failed; find_all is not used in its place (9 to 13 ms each second)."""


def _actors(class_name: str, world: Any) -> list:
    actors, way = reads.search(class_name, world)
    if way != "actors":
        raise SearchUnavailable(way)
    return list(islice(actors, MAX_FOUND))


def found(world: Any) -> list:
    """The time of day's post process and every volume that sets the saturation, MAX_FOUND at most."""
    parts = [actor.PostProcessComponent for actor in _actors(TIME_OF_DAY, world)]
    candidates = [part for part in parts if part is not None] + _actors(VOLUME, world)
    return [item for item in candidates if item.Settings.bOverride_ColorSaturation is True][:MAX_FOUND]


def path(item: Any) -> str | None:
    """The object's full path, which names it among the levels loaded; None when unread."""
    try:
        return str(item._path_name())
    except Exception:
        return None


def saturation(item: Any) -> tuple[float, float, float, float]:
    vector = item.Settings.ColorSaturation
    return tuple(float(getattr(vector, axis)) for axis in "XYZW")


def same(first: tuple, second: tuple) -> bool:
    return len(first) == len(second) and all(abs(a - b) <= TOLERANCE for a, b in zip(first, second))


def valid(values: tuple) -> bool:
    return len(values) == 4 and all(type(v) is float and math.isfinite(v) and SMALLEST <= v <= LARGEST
                                    for v in values)


def write(item: Any, values: tuple) -> bool:
    """Sets the saturation in place and reads it back: whether it held. ValueError before anything is set when the
    values are no saturation."""
    if not valid(values):
        raise ValueError(f"refused saturation {values}")
    item.Settings.ColorSaturation = unrealsdk.make_struct("Vector4", X=values[0], Y=values[1], Z=values[2],
                                                          W=values[3])
    return same(saturation(item), values)
