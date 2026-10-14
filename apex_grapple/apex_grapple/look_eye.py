"""The camera of the frame the game is drawing, through the eyes: where the arms' muzzle is measured from.

The game fills the camera it hands out only once every actor has moved. Read during the body's animation update,
where the mod runs, it is the camera of the frame before: its clock was the previous frame's in all 11 377 frames of
docs/apex_grapple/pistolet-grappin/sondes/vue_en_vol_essai.py (14 October 2026, verified in game). The character
and the arms have already moved: 35 cm on the median fast frame of a pull, up to 123. A muzzle found against that
camera left the rope beside the pistol as soon as Vex steered (Kevin, 14 October). The camera is therefore moved by
the character's step since the frame it was filled in (0.25 cm off on the median fast frame, 2.3 at most, against
the next frame's camera) and turned as the player turns now (the controller: within 1 degree, against 6.5 for the
camera as read). Without the character seen in that frame, the camera is taken as the game gives it.
"""

import math
from typing import Any

import unrealsdk

Spot = tuple[float, float, float]

# The camera's clock is kept in single precision, the game's in double: after an hour of play they part by a
# thousandth of a second, a frame lasting at least five.
SAME_FRAME_S = 0.004
KEPT_FRAMES = 2

# Where the character was in the last frames, by the game's clock.
_seen: dict[float, Spot] = {}


def _clock(character: Any) -> float:
    return float(unrealsdk.find_class("GameplayStatics").ClassDefaultObject.GetTimeSeconds(character))


def _location(character: Any) -> Spot:
    spot = character.K2_GetActorLocation()
    return float(spot.X), float(spot.Y), float(spot.Z)


def note(pc: Any) -> None:
    """Remembers where the character is in this frame: the camera filled at its end is the one the next frame reads.
    Called every frame the look is ours, shot or not."""
    character = pc.OakCharacter
    _seen[_clock(character)] = _location(character)
    for old in sorted(_seen)[:-KEPT_FRAMES]:
        del _seen[old]


def camera(pc: Any) -> tuple[Spot, tuple[Spot, Spot, Spot]]:
    """The camera's place in the frame being drawn, and its axes ahead, left and up; its roll is left out."""
    note(pc)
    manager = pc.PlayerCameraManager
    where = manager.GetCameraLocation()
    eye = (float(where.X), float(where.Y), float(where.Z))
    filled = float(manager.CameraCachePrivate.Timestamp)
    frame = next((clock for clock in _seen if abs(clock - filled) <= SAME_FRAME_S), None)
    if frame is not None:
        here = _location(pc.OakCharacter)
        eye = tuple(eye[axis] + here[axis] - _seen[frame][axis] for axis in range(3))
    turn = pc.ControlRotation
    pitch, yaw = math.radians(float(turn.Pitch)), math.radians(float(turn.Yaw))
    ahead = (math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch))
    # Unreal's Y is to the right: left is its opposite.
    left = (math.sin(yaw), -math.cos(yaw), 0.0)
    up = (-math.sin(pitch) * math.cos(yaw), -math.sin(pitch) * math.sin(yaw), math.cos(pitch))
    return eye, (ahead, left, up)


def forget() -> None:
    _seen.clear()
