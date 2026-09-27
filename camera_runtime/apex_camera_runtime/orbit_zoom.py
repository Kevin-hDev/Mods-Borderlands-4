"""Owned post-animation Orbit offset; interruptions never change the saved distance."""

import math
from typing import Any

from .constants import ORBIT_MODE
from .orbit_zoom_values import (DISTANCE_STEP, FRAME, MAX_DISTANCE, MIN_DISTANCE,
                               NATIVE_DISTANCE, OFFSET_TOLERANCE, valid_distance)


class OrbitZoom:
    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.identifier = controller.identifier + ":orbit_zoom"
        self.installed = False
        self.last_offset = None
        self.animation_ref = None
        self.animation_id = 0
        self.settings = None
        self.faulted = False

    @property
    def pending(self) -> bool:
        return self.installed or self.last_offset is not None

    def available(self) -> bool:
        owner = self.controller
        pc = owner._lifetime.pc_ref() if owner._lifetime.pc_ref else None
        actor, manager = owner._lifetime.owned()
        actor_id = owner._lifetime.address(getattr(pc, "OakCharacter", None))
        manager_id = owner._lifetime.address(getattr(pc, "PlayerCameraManager", None))
        return (not self.faulted and owner._bridge_started and owner._hooks_installed
                and not owner.cleanup_retry.pending and not owner.cleanup_retry.exhausted
                and self.settings is not None and self.settings.third_person_enabled()
                and self.settings.orbit_enabled() and pc is not None and actor is not None
                and actor_id == owner._lifetime.ids[1]
                and manager_id == owner._lifetime.ids[2]
                and owner._desired_mode == ORBIT_MODE and owner.orbit_available())

    def sync(self, settings: Any) -> None:
        self.settings = settings
        if (self.installed or not callable(getattr(settings, "orbit_distance", None))
                or not self.available()):
            return
        actor, _manager = self.controller._lifetime.owned()
        animation = actor.Mesh.GetAnimInstance()
        if animation is None:
            return
        self.animation_ref = self.controller.weak_ref(animation)
        self.animation_id = self.controller._lifetime.address(animation)
        self.installed = True
        self.controller.hooks.add_hook(
            FRAME, self.controller.hooks.Type.POST, self.identifier, self.on_frame)

    def _write(self, distance: float) -> None:
        if not valid_distance(distance):
            raise ValueError("invalid orbit distance")
        _actor, manager = self.controller._lifetime.owned()
        offset = manager.CameraModeState.CameraLocationOffset
        self.last_offset = NATIVE_DISTANCE - distance
        offset.X = self.last_offset
        if not math.isclose(float(offset.X), self.last_offset, abs_tol=OFFSET_TOLERANCE):
            raise RuntimeError("orbit distance refused")

    def release(self) -> None:
        if self.last_offset is None:
            return
        _actor, manager = self.controller._lifetime.owned()
        if manager is not None:
            offset = manager.CameraModeState.CameraLocationOffset
            # Only undo our own last write; another camera may already have replaced it.
            if math.isclose(float(offset.X), self.last_offset, abs_tol=OFFSET_TOLERANCE):
                offset.X = 0.0
                if not math.isclose(float(offset.X), 0.0, abs_tol=OFFSET_TOLERANCE):
                    raise RuntimeError("orbit distance cleanup refused")
        self.last_offset = None

    def on_frame(self, obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
        if (self.faulted or not self.installed or not self.animation_id
                or self.controller._lifetime.address(obj) != self.animation_id):
            return
        try:
            if self.available():
                self._write(self.settings.orbit_distance())
            else:
                self.release()
        except Exception:
            self.faulted = True
            self.controller.log("orbit zoom stopped after camera update failure")
            try:
                self.controller.stop()
            except Exception:
                # stop owns the bounded cleanup retry; never keep writing from this callback.
                self.controller.log("orbit zoom cleanup pending")

    def change(self, settings: Any, direction: int) -> bool:
        if type(direction) is not int or direction not in (-1, 1) or not self.available():
            return False
        previous = settings.orbit_distance()
        if not valid_distance(previous):
            return False
        distance = min(MAX_DISTANCE, max(MIN_DISTANCE, previous + direction * DISTANCE_STEP))
        if distance == previous:
            return True
        try:
            self._write(distance)
            settings.set_orbit_distance(distance)
        except Exception:
            try:
                self._write(previous)
            except Exception:
                self.controller.stop()
                raise
            return False
        self.controller.log(f"orbit zoom distance={distance:g}")
        return True

    def stop(self, stale: bool = False) -> None:
        self.faulted = True
        hooks = self.controller.hooks
        if self.installed:
            if hooks.has_hook(FRAME, hooks.Type.POST, self.identifier):
                hooks.remove_hook(FRAME, hooks.Type.POST, self.identifier)
            self.installed = False
        try:
            self.release()
        except Exception:
            if not stale:
                raise
            self.last_offset = None
            self.controller.log("stale Orbit zoom offset abandoned after map or character change")
        self.animation_ref = self.settings = None
        self.animation_id = 0
        self.faulted = False
