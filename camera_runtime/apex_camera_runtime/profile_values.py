"""The five settings a camera profile holds (Kevin, 2026-10-12: « les réglages customisables au pourcentage près »): the
field of view, the close and far distances, the shoulder spacing and the camera height.

Their bounds are the sliders' own, read where those sliders are defined, so a profile never holds what the menu could
not set (docs/third_person_fov/camera/2026-10-12-conception-profils-camera.md).
"""

import math
from dataclasses import dataclass, replace

from .camera_distance_options import CLOSE_M, FAR_M, MAX_CLOSE_M, MAX_FAR_M, MIN_CLOSE_M, MIN_FAR_M
from .constants import FOV_DEFAULT, FOV_MAX, FOV_MIN
from .framing_catalog import GROUPS, group

FIELDS = ("fov", "close", "far", "spacing", "height")
SPACING, HEIGHT = group("horizontal"), group("height")


@dataclass(frozen=True)
class Values:
    fov: int
    # Metres to the centimetre, as the CAMERA VIEW sliders show them.
    close: float
    far: float
    # Percent, as framing_catalog.py defines them.
    spacing: int
    height: int


DEFAULTS = Values(int(FOV_DEFAULT), CLOSE_M, FAR_M, SPACING.default, HEIGHT.default)


def _number(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except OverflowError:
        # An integer past a float's range: only a file edited by hand holds one.
        return None
    return number if math.isfinite(number) else None


def checked(field: str, value):
    """The value as a profile keeps it, or ValueError: a value past its slider is refused rather than clamped, so a
    file edited by hand cannot pass for the player's choice."""
    number = _number(value)
    if number is None:
        raise ValueError(f"invalid profile {field}")
    if field == "fov":
        if not number.is_integer() or not FOV_MIN <= number <= FOV_MAX:
            raise ValueError("invalid profile fov")
        return int(number)
    if field in ("close", "far"):
        low, high = (MIN_CLOSE_M, MAX_CLOSE_M) if field == "close" else (MIN_FAR_M, MAX_FAR_M)
        number = round(number, 2)
        if not low <= number <= high:
            raise ValueError(f"invalid profile {field}")
        return number
    if field in ("spacing", "height"):
        if not number.is_integer() or not (SPACING if field == "spacing" else HEIGHT).valid(int(number)):
            raise ValueError(f"invalid profile {field}")
        return int(number)
    raise ValueError("unknown profile field")


def make(**fields) -> Values:
    if set(fields) != set(FIELDS):
        raise ValueError("incomplete profile values")
    return Values(**{field: checked(field, fields[field]) for field in FIELDS})


def changed(values: Values, field: str, value) -> Values:
    if field not in FIELDS:
        raise ValueError("unknown profile field")
    return replace(values, **{field: checked(field, value)})


def _or_default(field: str, value):
    try:
        return checked(field, value)
    except ValueError:
        return getattr(DEFAULTS, field)


def _read(settings, name: str):
    read = getattr(settings, name, None)
    return read() if callable(read) else None


def from_camera(settings, shown_fov) -> Values:
    """What the camera shows now, from the elected mod's settings, as a new profile's start: the FOV on screen (the
    game's while the mod's own is off, fov.py), else the mod's FOV, else 110. A reading a profile could not hold, or a
    mod older than one of these settings, starts that value at its default."""
    fov = _number(shown_fov)
    if fov is None and _read(settings, "fov_enabled") is True:
        fov = _number(_read(settings, "fov_value"))
    distances = _read(settings, "camera_distances")
    close, far = (distances[0], distances[2]) if type(distances) is tuple and len(distances) == 3 else (None, None)
    framing = _read(settings, "framing_values")
    rows = dict(zip((item.key for item in GROUPS), framing)) if type(framing) is tuple else {}
    placed = {key: row[0] if type(row) is tuple and row else None for key, row in rows.items()}
    read = {"fov": None if fov is None else round(min(FOV_MAX, max(FOV_MIN, fov))),
            "close": None if _number(close) is None else close / 100,
            "far": None if _number(far) is None else far / 100,
            "spacing": placed.get(SPACING.key), "height": placed.get(HEIGHT.key)}
    return Values(**{field: _or_default(field, read[field]) for field in FIELDS})
