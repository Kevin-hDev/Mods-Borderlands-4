"""The one writer of the camera manager's CameraLocationOffset on foot (dynamic camera plan, 2026-10-06).

It sums what is asked of the offset each frame: in Orbit, the zoom's distance (orbit_zoom.py, which no longer writes
itself); in ThirdPerson, the framing by action and the camera motion (dynamic_camera.py). Two writers on one field
would end up contradicting each other. The game puts the offset back to zero each frame and checks walls after it
(verified in game, 2026-09-26, releves/third_person_fov/2026-09-26-zoom-orbit): once nothing is asked, nothing stays.
It writes at the hunter's animation update, as the Orbit zoom did: the offset read there was zero at every frame of
the framing trial, so the write comes before the camera is placed. Interruptions never change a saved setting.
"""

import math
from typing import Any

from .constants import ORBIT_MODE, THIRD_PERSON_MODE
from .dynamic_camera import DynamicCamera
from .orbit_zoom_values import FRAME, OFFSET_TOLERANCE
from .player_sample import read

AXES = ("X", "Y", "Z")


class CameraOffset:
    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.identifier = controller.identifier + ":camera_offset"
        self.installed = False
        # Our last write, axis by axis: only the axes we wrote are ever given back.
        self.written: dict[str, float] | None = None
        self.animation_ref = None
        self.animation_id = 0
        self.settings = None
        self.faulted = False
        self.dynamic = DynamicCamera()

    @property
    def pending(self) -> bool:
        return self.installed or self.written is not None

    def ready(self) -> bool:
        owner = self.controller
        return (not self.faulted and owner._bridge_started and owner._hooks_installed
                and not owner.cleanup_retry.pending and not owner.cleanup_retry.exhausted
                and self.settings is not None)

    def sync(self, settings: Any) -> None:
        self.settings = settings
        if self.installed or not self.ready():
            return
        if not (callable(getattr(settings, "orbit_distance", None))
                or callable(getattr(settings, "dynamic_camera", None))):
            return
        actor, _manager = self.controller._lifetime.owned()
        animation = actor.Mesh.GetAnimInstance() if actor is not None else None
        if animation is None:
            return
        self.animation_ref = self.controller.weak_ref(animation)
        self.animation_id = self.controller._lifetime.address(animation)
        self.installed = True
        self.controller.hooks.add_hook(FRAME, self.controller.hooks.Type.POST, self.identifier, self.on_frame)

    def write(self, values: dict[str, float]) -> None:
        _actor, manager = self.controller._lifetime.owned()
        offset = manager.CameraModeState.CameraLocationOffset
        for axis, value in values.items():
            setattr(offset, axis, value)
        self.written = dict(values)
        if any(not math.isclose(float(getattr(offset, axis)), value, abs_tol=OFFSET_TOLERANCE)
               for axis, value in values.items()):
            raise RuntimeError("camera offset refused")

    def release(self) -> None:
        if self.written is None:
            return
        _actor, manager = self.controller._lifetime.owned()
        if manager is not None:
            offset = manager.CameraModeState.CameraLocationOffset
            # Only our own last write: another camera may already have replaced it.
            for axis, value in self.written.items():
                if math.isclose(float(getattr(offset, axis)), value, abs_tol=OFFSET_TOLERANCE):
                    setattr(offset, axis, 0.0)
                    if not math.isclose(float(getattr(offset, axis)), 0.0, abs_tol=OFFSET_TOLERANCE):
                        raise RuntimeError("camera offset cleanup refused")
        self.written = None

    def wanted(self, now_ns: int) -> dict[str, float] | None:
        orbit = self.controller.zoom.wanted_x()
        if orbit is not None:
            self.dynamic.reset()
            return {"X": orbit}
        offset = self._dynamic(now_ns)
        return None if offset is None else dict(zip(AXES, offset))

    def _dynamic(self, now_ns: int) -> tuple | None:
        owner = self.controller
        read_values = getattr(self.settings, "dynamic_camera", None)
        actor, manager = owner._lifetime.owned()
        if (not callable(read_values) or actor is None or owner._in_vehicle
                or owner._desired_mode == ORBIT_MODE
                or str(manager.GetActorCameraMode(actor)) != THIRD_PERSON_MODE):
            self.dynamic.reset()
            return None
        rotation = manager.GetCameraRotation()
        pc = owner._lifetime.pc_ref() if owner._lifetime.pc_ref else None
        return self.dynamic.step(read_values(), read(pc), float(rotation.Pitch), float(rotation.Yaw), now_ns)

    def on_frame(self, obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
        if (self.faulted or not self.installed or not self.animation_id
                or self.controller._lifetime.address(obj) != self.animation_id):
            return
        try:
            values = self.wanted(self.controller.clock()) if self.ready() else None
            if values is None:
                self.release()
            else:
                self.write(values)
        except Exception:
            self.faulted = True
            self.controller.log("camera offset stopped after camera update failure")
            try:
                self.controller.stop()
            except Exception:
                # stop owns the bounded cleanup retry; never keep writing from this callback.
                self.controller.log("camera offset cleanup pending")

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
            self.written = None
            self.controller.log("stale camera offset abandoned after map or character change")
        self.animation_ref = self.settings = None
        self.animation_id = 0
        self.dynamic.reset()
        self.faulted = False
