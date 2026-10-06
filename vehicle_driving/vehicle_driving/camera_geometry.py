"""Where the top of the driver sits seen from the camera, and the offset that zooms about it (spec section 3.8).

The camera manager's CameraLocationOffset follows the camera's own axes, pitch included: verified in game in trial 4
(docs/investigations/vehicle_driving/camera/2026-10-06-distance-camera-vehicule.md), where zooming about the top of the
driver held it 4.6 to 5.5 degrees under the reticle in every view.
"""

import math
from typing import Any

ZERO = (0.0, 0.0, 0.0)
# Half the driver's capsule when it cannot be read: the top of a standing character, above a seated one's head.
HALF_HEIGHT = 90.0


def point(vector: Any) -> tuple[float, float, float] | None:
    values = (float(vector.X), float(vector.Y), float(vector.Z))
    return values if all(math.isfinite(value) for value in values) else None


def basis(rotation: Any) -> tuple:
    """Forward, right and up of a camera rotation, the axes the offset follows (roll left out)."""
    pitch, yaw = math.radians(float(rotation.Pitch)), math.radians(float(rotation.Yaw))
    forward = (math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch))
    right = (-math.sin(yaw), math.cos(yaw), 0.0)
    up = (-math.sin(pitch) * math.cos(yaw), -math.sin(pitch) * math.sin(yaw), math.cos(pitch))
    return forward, right, up


def to_camera(vector: tuple, axes: tuple) -> tuple[float, float, float]:
    return tuple(sum(a * b for a, b in zip(vector, axis)) for axis in axes)


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
    return to_camera(tuple(a - b for a, b in zip(top, camera)), axes)


def below_reticle(seen: tuple) -> float:
    """How many degrees the top of the driver sits under the reticle, the centre of the screen."""
    return math.degrees(math.atan2(-seen[2], seen[0]))


def zoomed(seen: tuple, applied: tuple, share: float) -> tuple[float, float, float]:
    """The offset that puts the camera at share times the game's distance from the top of the driver.

    seen is measured from the camera last drawn, which carries the offset the game applied then: adding it back gives
    the top of the driver seen from the game's own camera, whatever was written before.
    """
    game = tuple(value + offset for value, offset in zip(seen, applied))
    return tuple((1.0 - share) * value for value in game)
