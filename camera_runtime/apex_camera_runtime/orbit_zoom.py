"""The Orbit distance asked of the camera offset; interruptions never change the saved distance.

Since the dynamic camera (2026-10-06) camera_offset.py is the offset's one writer: this module says what the Orbit
distance asks for, and writes only through it.
"""

from typing import Any

from .constants import ORBIT_MODE
from .orbit_zoom_values import DISTANCE_STEP, MAX_DISTANCE, MIN_DISTANCE, NATIVE_DISTANCE, valid_distance


class OrbitZoom:
    def __init__(self, controller: Any) -> None:
        self.controller = controller

    @property
    def settings(self) -> Any:
        return self.controller.offset.settings

    def available(self) -> bool:
        owner = self.controller
        settings = self.settings
        pc = owner._lifetime.pc_ref() if owner._lifetime.pc_ref else None
        actor, manager = owner._lifetime.owned()
        actor_id = owner._lifetime.address(getattr(pc, "OakCharacter", None))
        manager_id = owner._lifetime.address(getattr(pc, "PlayerCameraManager", None))
        return (owner.offset.ready() and settings.orbit_enabled() and pc is not None and actor is not None
                and actor_id == owner._lifetime.ids[1]
                and manager_id == owner._lifetime.ids[2]
                and owner._desired_mode == ORBIT_MODE and owner.orbit_available())

    def wanted_x(self) -> float | None:
        """The offset that puts the camera at the saved distance (the game adds it to its own 300), or None."""
        if not (callable(getattr(self.settings, "orbit_distance", None)) and self.available()):
            return None
        return _offset(self.settings.orbit_distance())

    def change(self, settings: Any, direction: int) -> bool:
        if type(direction) is not int or direction not in (-1, 1) or not self.available():
            return False
        previous = settings.orbit_distance()
        if not valid_distance(previous):
            return False
        distance = min(MAX_DISTANCE, max(MIN_DISTANCE, previous + direction * DISTANCE_STEP))
        if distance == previous:
            return True
        writer = self.controller.offset
        try:
            writer.write({"X": _offset(distance)})
            settings.set_orbit_distance(distance)
        except Exception:
            try:
                writer.write({"X": _offset(previous)})
            except Exception:
                self.controller.stop()
                raise
            return False
        self.controller.log(f"orbit zoom distance={distance:g}")
        return True


def _offset(distance: float) -> float:
    if not valid_distance(distance):
        raise ValueError("invalid orbit distance")
    return NATIVE_DISTANCE - distance
