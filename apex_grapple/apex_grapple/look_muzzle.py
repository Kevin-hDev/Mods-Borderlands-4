"""Where the grapple gun's muzzle is in the world: where the rope leaves and where the hook comes back.

From behind, the body's pistol's muzzle. Through the eyes, the game draws the arms at a field of view of their own, the
world at the player's (77 degrees against Kevin's 110, read in game on 2026-09-23): a spot of the arms shows farther
from the middle of the screen than the same spot of the world. The muzzle is moved to the spot of the world that shows
where the arms show it, kept as far ahead and pushed away from the camera's axis by the ratio of the two views'
half-angle tangents, both read at each call (Benefix Ohm Attack's arms_view.py, verified in game on its beam; a copy
of ours, since a mod never depends on another), against the camera of the frame being drawn (look_eye.py). While
the arms' pistol is hidden, before the arm comes in and once it is out, the muzzle waits at a fixed place below the
screen (look_assets.MUZZLE_IN_CM, MUZZLE_OUT_CM, measured on the validated video's arms): never at the hand leaving the weapon, which passes the face (drawings of 14 October).

A piece's muzzle is in its own axes as the game has them (look_assets.PIECES, muzzle_cm), turned and moved as the piece
is in the world; the pieces hang at size 1.
"""

import math
from typing import Any

from . import look_eye

# A field of view outside these is a misread, not a view: its tangent would send the spot nowhere.
MIN_ANGLE, MAX_ANGLE = 10.0, 170.0

Spot = tuple[float, float, float]


def fields(pc: Any) -> tuple[float, float]:
    """The world's field of view and the arms', in degrees, read now."""
    manager = pc.PlayerCameraManager
    world, arms = float(manager.GetFOVAngle()), float(manager.CameraModeState.ViewModelFOV)
    if not all(MIN_ANGLE <= angle <= MAX_ANGLE for angle in (world, arms)):
        raise ValueError(f"fields of view out of bounds: world {world!r}, arms {arms!r}")
    return world, arms


def from_arms(pc: Any, spot: Spot) -> Spot:
    """The spot of the world that shows where the arms show `spot`."""
    eye, (ahead, _left, _up) = look_eye.camera(pc)
    world, arms = fields(pc)
    spread = math.tan(math.radians(world) / 2) / math.tan(math.radians(arms) / 2)
    along = sum((spot[axis] - eye[axis]) * ahead[axis] for axis in range(3))
    on_axis = tuple(eye[axis] + ahead[axis] * along for axis in range(3))
    return tuple(on_axis[axis] + (spot[axis] - on_axis[axis]) * spread for axis in range(3))


def waiting(pc: Any, offset_cm: tuple) -> Spot:
    """The muzzle of the hidden arms' pistol: `offset_cm` (ahead, left, up) from the eye, as the arms show it."""
    eye, axes = look_eye.camera(pc)
    spot = tuple(eye[axis] + sum(offset * way[axis] for offset, way in zip(offset_cm, axes)) for axis in range(3))
    return from_arms(pc, spot)


def on_piece(made: Any, muzzle_cm: tuple) -> Spot:
    """A piece's muzzle in the world, as Unreal turns a rotator (FRotationMatrix's axes)."""
    where, turn = made.K2_GetComponentLocation(), made.K2_GetComponentRotation()
    sp, cp = math.sin(math.radians(float(turn.Pitch))), math.cos(math.radians(float(turn.Pitch)))
    sy, cy = math.sin(math.radians(float(turn.Yaw))), math.cos(math.radians(float(turn.Yaw)))
    sr, cr = math.sin(math.radians(float(turn.Roll))), math.cos(math.radians(float(turn.Roll)))
    axes = ((cp * cy, cp * sy, sp), (sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp),
            (-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp))
    origin = (float(where.X), float(where.Y), float(where.Z))
    return tuple(origin[axis] + sum(offset * way[axis] for offset, way in zip(muzzle_cm, axes)) for axis in range(3))
