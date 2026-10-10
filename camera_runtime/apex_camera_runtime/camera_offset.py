"""The one writer of the camera manager's CameraLocationOffset on foot (dynamic camera plan, 2026-10-06).

It sums what is asked of the offset each frame: in Orbit, the zoom's distance (orbit_zoom.py, which no longer writes
itself); in ThirdPerson, the framing by action, the camera motion and the chosen camera distance (dynamic_camera.py);
and the shoulder while it shows (shoulder_offset.py). Two writers on one field
would end up contradicting each other. The game puts the offset back to zero each frame and checks walls after it
(verified in game, 2026-09-26, releves/third_person_fov/2026-09-26-zoom-orbit; for the shoulder, 2026-10-08, third
trial of docs/third_person_fov/camera/enquetes/2026-10-08-sauts-camera-collisions.md): once nothing is asked, nothing
stays.
It writes at the hunter's animation update, as the Orbit zoom did: the offset read there was zero at every frame of
the framing trial, so the write comes before the camera is placed. Interruptions never change a saved setting.
"""

import math
from typing import Any

from .camera_distance import DISTANCES, offset as distance_offset
from .constants import ORBIT_MODE, THIRD_PERSON_MODE
from .dynamic_camera import DynamicCamera
from .orbit_zoom_values import FRAME, OFFSET_TOLERANCE
from .player_sample import read
from .shoulder_offset import framing_share

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
        # Every mod's third person needs the hook now: the shoulder goes through it, with or without the other offsets.
        if not self.ready():
            return
        actor, _manager = self.controller._lifetime.owned()
        # A hunter without its mesh yet has no animation to hook: the next frame tries again.
        mesh = getattr(actor, "Mesh", None)
        animation = mesh.GetAnimInstance() if mesh is not None else None
        if animation is None:
            return
        address = self.controller._lifetime.address(animation)
        if self.installed:
            # The same hunter can get a new animation: Hunter Change's looks give one (verified in game, 2026-10-07,
            # releves/2026-10-07-distance/sdk-essai-2-curseurs.log). Kept on the old one, the offset never wrote again.
            if address != self.animation_id:
                self.animation_ref, self.animation_id = self.controller.weak_ref(animation), address
            return
        self.animation_ref = self.controller.weak_ref(animation)
        self.animation_id = address
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
        """The mod's other offsets end here (climbing, aiming in Orbit); the shoulder stays while it shows, so its
        glide out is not cut by a frame without it."""
        shoulder = self._shoulder() if self.installed and self.ready() else None
        if shoulder is None:
            self._clear()
        else:
            self.write(shoulder)

    def _clear(self) -> None:
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
            values = {"X": orbit}
        else:
            offset = self._dynamic(now_ns)
            values = None if offset is None else dict(zip(AXES, offset))
        shoulder = self._shoulder()
        if shoulder is None:
            return values
        values = dict(values or {})
        for axis, value in shoulder.items():
            values[axis] = values.get(axis, 0.0) + value
        return values

    def _shoulder(self) -> dict[str, float] | None:
        """The shoulder's share while it shows in this mode (shoulder_offset.py), None otherwise."""
        owner = self.controller
        shoulder = getattr(owner.bridge, "shoulder", None)
        if shoulder is None:
            return None
        actor, manager = owner._lifetime.owned()
        if actor is None or manager is None or owner._in_vehicle or not shoulder.allows(manager, actor):
            shoulder.withhold()
            return None
        side, up = shoulder.place(*framing_share(self.settings))
        return {"Y": side, "Z": up} if side or up else None

    def _dynamic(self, now_ns: int) -> tuple | None:
        owner = self.controller
        read_values = getattr(self.settings, "dynamic_camera", None)
        # Mods older than the camera distance key (2026-10-07) have no distance to read: the game's own.
        read_distance = getattr(self.settings, "camera_distance", None)
        read_lengths = getattr(self.settings, "camera_distances", None)
        actor, manager = owner._lifetime.owned()
        # Climbing drops these offsets at once (camera_frame.py), even before the game's mode changes.
        if (not (callable(read_values) or callable(read_distance)) or actor is None or owner._in_vehicle
                or owner._desired_mode == ORBIT_MODE or getattr(getattr(owner, "climb", None), "busy", False)
                or str(manager.GetActorCameraMode(actor)) != THIRD_PERSON_MODE):
            self.dynamic.reset()
            return None
        rotation = manager.GetCameraRotation()
        pc = owner._lifetime.pc_ref() if owner._lifetime.pc_ref else None
        values = read_values() if callable(read_values) else (0.0, 0.0)
        lengths = read_lengths() if callable(read_lengths) else DISTANCES
        distance = distance_offset(read_distance(), lengths) if callable(read_distance) else 0.0
        return self.dynamic.step(values, read(pc), float(rotation.Pitch), float(rotation.Yaw), now_ns, distance)

    def on_frame(self, obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
        if (self.faulted or not self.installed or not self.animation_id
                or self.controller._lifetime.address(obj) != self.animation_id):
            return
        try:
            values = self.wanted(self.controller.clock()) if self.ready() else None
            if values is None:
                self._clear()
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
            self._clear()
        except Exception:
            if not stale:
                raise
            self.written = None
            self.controller.log("stale camera offset abandoned after map or character change")
        self.animation_ref = self.settings = None
        self.animation_id = 0
        self.dynamic.reset()
        self.faulted = False
