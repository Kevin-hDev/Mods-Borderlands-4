"""Where the top of the driver sits seen from the camera, and the offset that zooms about it (spec section 3.8).

The camera manager's CameraLocationOffset follows the camera's own axes, pitch included: verified in game in trial 4
(docs/investigations/vehicle_driving/camera/2026-10-06-distance-camera-vehicule.md), where zooming about the top of the
driver held it 4.6 to 5.5 degrees under the reticle in every view.

Run at every frame a view writes: each formula is written out, the same operations in the same order as up to 1.0.11,
so the numbers are the same to the last digit (test_camera_geometry.py) for fewer steps.
"""

import math
from typing import Any

ZERO = (0.0, 0.0, 0.0)
# Half the driver's capsule when it cannot be read: the top of a standing character, above a seated one's head.
HALF_HEIGHT = 90.0


def point(vector: Any) -> tuple[float, float, float] | None:
    x, y, z = float(vector.X), float(vector.Y), float(vector.Z)
    return (x, y, z) if math.isfinite(x) and math.isfinite(y) and math.isfinite(z) else None


def basis(rotation: Any) -> tuple:
    """Forward, right and up of a camera rotation, the axes the offset follows (roll left out)."""
    pitch, yaw = math.radians(float(rotation.Pitch)), math.radians(float(rotation.Yaw))
    cos_pitch, sin_pitch, cos_yaw, sin_yaw = math.cos(pitch), math.sin(pitch), math.cos(yaw), math.sin(yaw)
    forward = (cos_pitch * cos_yaw, cos_pitch * sin_yaw, sin_pitch)
    right = (-sin_yaw, cos_yaw, 0.0)
    up = (-sin_pitch * cos_yaw, -sin_pitch * sin_yaw, cos_pitch)
    return forward, right, up


def to_camera(vector: tuple, axes: tuple) -> tuple[float, float, float]:
    # sum() kept: since Python 3.12 it adds floats with compensation, which a chain of + does not.
    x, y, z = vector
    forward, right, up = axes
    return (sum((x * forward[0], y * forward[1], z * forward[2])),
            sum((x * right[0], y * right[1], z * right[2])),
            sum((x * up[0], y * up[1], z * up[2])))


def driver_top(vehicle: Any) -> tuple[float, float, float] | None:
    """The top of the driver's capsule, or None while the driver cannot be read (a normal state, not an error)."""
    try:
        driver = vehicle.DriverPawn
        body = point(driver.K2_GetActorLocation())
    except Exception:
        return None
    if body is None:
        return None
    try:
        half = float(driver.CapsuleComponent.GetScaledCapsuleHalfHeight())
    except Exception:
        half = HALF_HEIGHT
    if not math.isfinite(half) or not 0.0 < half < 500.0:
        half = HALF_HEIGHT
    return body[0], body[1], body[2] + half


def sighting(vehicle: Any, manager: Any) -> tuple[float, float, float] | None:
    """The top of the driver in the axes of the camera last drawn (forward, right, up), or None when unreadable."""
    try:
        camera = point(manager.GetCameraLocation())
        axes = basis(manager.GetCameraRotation())
    except Exception:
        return None
    top = driver_top(vehicle)
    if camera is None or top is None:
        return None
    return to_camera((top[0] - camera[0], top[1] - camera[1], top[2] - camera[2]), axes)


def below_reticle(seen: tuple) -> float:
    """How many degrees the top of the driver sits under the reticle, the centre of the screen."""
    return math.degrees(math.atan2(-seen[2], seen[0]))


def zoomed(seen: tuple, applied: tuple, share: float) -> tuple[float, float, float]:
    """The offset that puts the camera at share times the game's distance from the top of the driver.

    seen is measured from the camera last drawn, which carries the offset the game applied then: adding it back gives
    the top of the driver seen from the game's own camera, whatever was written before.
    """
    keep = 1.0 - share
    return keep * (seen[0] + applied[0]), keep * (seen[1] + applied[1]), keep * (seen[2] + applied[2])
