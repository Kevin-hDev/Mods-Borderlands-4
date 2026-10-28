"""The fake camera manager of Vehicle Driving's test SDK."""

import types
from typing import Any


def _vector(x: float, y: float, z: float) -> Any:
    return types.SimpleNamespace(X=x, Y=y, Z=z)


class CameraManager:
    """The player's camera manager at the wheel. The game draws its camera at `base` plus the offset left at the end
    of the last frame, in world axes (the camera's own at pitch 0 and yaw 0), then sets the offset back to 0 (trials 2
    to 4, 2026-10-06). Seen from `base`, the top of the default driver is (400, 0, -10)."""

    def __init__(self) -> None:
        self.base = _vector(-300.0, 200.0, 260.0)
        self.location = self.base
        self.rotation = types.SimpleNamespace(Pitch=0.0, Yaw=0.0, Roll=0.0)
        self.CameraModeState = types.SimpleNamespace(CameraLocationOffset=_vector(0.0, 0.0, 0.0))

    def GetCameraLocation(self) -> Any:
        return self.location

    def GetCameraRotation(self) -> Any:
        return self.rotation

    def draw(self) -> None:
        """One frame drawn by the game: the camera takes the offset, which goes back to 0."""
        offset = self.CameraModeState.CameraLocationOffset
        self.location = _vector(self.base.X + offset.X, self.base.Y + offset.Y, self.base.Z + offset.Z)
        offset.X = offset.Y = offset.Z = 0.0
