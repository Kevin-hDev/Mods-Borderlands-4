"""Where the world must hold a thing for it to show on the first-person arms.

The game draws the first-person arms at a field of view of their own, the world at the player's: 77 degrees
against Kevin's 110 (CameraModeState.ViewModelFOV and the camera's angle, read in game on 2026-09-23,
docs/investigations/omni_sprint/2026-09-23-omni-sprint-camera-fov.md). A spot of the arms therefore shows farther
from the middle of the screen than the same spot of the world does, and the beam, lit in the world at the palm's
socket, started beside the hand (Kevin's capture of 2026-10-01, docs/attaque-rayon/enquetes/
2026-10-01-depart-du-rayon.md).

The spot is kept as far ahead of the camera and pushed away from the camera's axis by the ratio of the two views'
half-angle tangents: the world then shows it where the arms show the hand. Both angles are read at each call,
never kept: the player's setting and aiming down sights change them.
"""

import math
from typing import Any

from . import aim, report

# A field of view outside these is a misread, not a view: its tangent would send the spot nowhere.
MIN_ANGLE, MAX_ANGLE = 10.0, 170.0

Spot = tuple[float, float, float]


def _spread(manager: Any) -> float:
    """How many times farther from the middle of the screen the arms show a spot than the world does."""
    world, arms = float(manager.GetFOVAngle()), float(manager.CameraModeState.ViewModelFOV)
    if not all(MIN_ANGLE <= angle <= MAX_ANGLE for angle in (world, arms)):
        raise ValueError(f"fields of view out of bounds: world {world!r}, arms {arms!r}")
    return math.tan(math.radians(world) / 2) / math.tan(math.radians(arms) / 2)


def shown(pc: Any, spot: Spot) -> Spot:
    """The spot of the world that shows where the arms show this spot of theirs; the spot itself, said once, when
    the two views cannot be read."""
    try:
        eye, turn = aim.eye(pc)
        way = aim.facing(turn)
        spread = _spread(pc.PlayerCameraManager)
        ahead = sum((spot[axis] - eye[axis]) * way[axis] for axis in range(3))
        on_axis = tuple(eye[axis] + way[axis] * ahead for axis in range(3))
        return tuple(on_axis[axis] + (spot[axis] - on_axis[axis]) * spread for axis in range(3))
    except Exception as error:
        report.error_once("arms view", f"the arms' view could not be read, the beam may start beside the hand: {error!r}")
        return spot
