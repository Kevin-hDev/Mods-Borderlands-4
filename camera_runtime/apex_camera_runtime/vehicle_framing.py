"""The framing at the wheel: the camera moves back with the vehicle's speed (dynamic camera, idea 2).

At the wheel the controller has no character, so the hunter's animation no longer clocks the camera runtime: any
animation update does, as in Vehicle Driving, and updates closer than MIN_STEP_NS are the same frame seen again. The
framing is published for Vehicle Driving every frame; this unit writes the offset only while Vehicle Driving does not
(vehicle_share.py). Kevin tried these values with the trial probe on 2026-10-06: « ça me convient ».
"""

import math
from typing import Any, Callable

from . import action_framing, vehicle_share
from .easing import MAX_STEP_S, Easing

FRAME = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
IDENTIFIER = "apex_camera_runtime:vehicle_framing"
MIN_STEP_NS = 3_000_000
TOLERANCE = 0.001
REST = 0.01


def _same(values: tuple, targets: tuple) -> bool:
    return all(math.isclose(value, target, abs_tol=TOLERANCE) for value, target in zip(values, targets))


def _read(offset: Any) -> tuple:
    return float(offset.X), float(offset.Y), float(offset.Z)


def vehicle_speed(vehicle: Any) -> float:
    velocity = vehicle.Mesh.GetPhysicsLinearVelocity("None")
    speed = math.hypot(float(velocity.X), float(velocity.Y))
    return speed if math.isfinite(speed) else 0.0


class VehicleFraming:
    def __init__(self, load: Callable) -> None:
        """load() gives (hooks, get_pc, weak_ref, address_of, clock, log), asked when the clock is first needed: the
        runtime exists before the game's modules can be read, as in the camera mods' tests."""
        self.load = load
        self.hooks = None
        self.settings = None
        self.installed = False
        self._forget()

    def _forget(self) -> None:
        self.easing = Easing(2, REST)
        self.vehicle_id = self.failed_id = 0
        self.top = 0.0
        self.last_ns = 0
        self.written: tuple | None = None
        self.manager_ref = None
        # Who writes at the wheel, logged when it changes: the trial with and without Vehicle Driving reads it.
        self.writer = ""

    def sync(self, settings: Any) -> None:
        """On foot, from the elected mod's frame: the clock runs while that mod's framing is on."""
        read_values = getattr(settings, "dynamic_camera", None)
        wanted = callable(read_values) and read_values()[0] > 0.0
        self.settings = settings if wanted else None
        if wanted and not self.installed:
            if self.hooks is None:
                (self.hooks, self.get_pc, self.weak_ref, self.address_of, self.clock,
                 self.log) = self.load()
            self.hooks.add_hook(FRAME, self.hooks.Type.POST, IDENTIFIER, self.on_frame)
            self.installed = True
        elif not wanted and self.installed:
            self.stop()

    def on_frame(self, _obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
        now_ns = self.clock()
        if now_ns - self.last_ns < MIN_STEP_NS:
            return
        step_s = 0.0 if not self.last_ns else min((now_ns - self.last_ns) / 1e9, MAX_STEP_S)
        self.last_ns = now_ns
        pc = self.get_pc(possibly_loading=True)
        vehicle = getattr(pc, "Pawn", None) if pc is not None else None
        if vehicle is None or getattr(vehicle, "OakVehicleMovement", None) is None or self.settings is None:
            self._leave()
            return
        vehicle_id = self.address_of(vehicle)
        if vehicle_id == self.failed_id:
            return
        try:
            self._step(pc, vehicle, vehicle_id, step_s)
        except Exception as error:
            # As Vehicle Driving's parts: one that raises stops alone until the next vehicle.
            self.failed_id = vehicle_id
            self.log(f"vehicle framing stopped until the next vehicle: {type(error).__name__}")
            self._release()

    def _step(self, pc: Any, vehicle: Any, vehicle_id: int, step_s: float) -> None:
        if vehicle_id != self.vehicle_id:
            self._release()
            self.vehicle_id, self.top, self.failed_id, self.writer = vehicle_id, 0.0, 0, ""
            self.easing.reset()
        speed = vehicle_speed(vehicle)
        self.top = max(self.top, speed)
        goal = action_framing.vehicle_target(speed, self.top, self.settings.dynamic_camera()[0])
        x, z = self.easing.step(goal, action_framing.SECONDS, step_s)
        framing = (x, 0.0, z)
        vehicle_share.publish(framing)
        self._note_writer("Vehicle Driving" if vehicle_share.claimed() else "camera mods")
        if vehicle_share.claimed():
            # Vehicle Driving writes its view plus this framing; its write replaces ours each frame.
            self.written = self.manager_ref = None
            return
        if framing == vehicle_share.ZERO:
            self._release()
            return
        manager = pc.PlayerCameraManager
        offset = manager.CameraModeState.CameraLocationOffset
        offset.X, offset.Y, offset.Z = framing
        if not _same(_read(offset), framing):
            raise RuntimeError("the game refused the camera offset")
        self.written, self.manager_ref = framing, self.weak_ref(manager)

    def _note_writer(self, writer: str) -> None:
        if writer != self.writer:
            self.writer = writer
            self.log(f"vehicle framing written by {writer}")

    def _leave(self) -> None:
        if self.vehicle_id or self.written is not None:
            self._release()
            vehicle_share.publish(vehicle_share.ZERO)
            self.vehicle_id, self.top, self.failed_id = 0, 0.0, 0
            self.easing.reset()

    def _release(self) -> None:
        """Only our own last write: the game sets the offset back each frame anyway, this spares the last one."""
        written, manager = self.written, self.manager_ref() if self.manager_ref is not None else None
        self.written = self.manager_ref = None
        if written is None or manager is None:
            return
        offset = manager.CameraModeState.CameraLocationOffset
        if _same(_read(offset), written):
            offset.X, offset.Y, offset.Z = vehicle_share.ZERO

    def stop(self) -> None:
        if self.installed:
            if self.hooks.has_hook(FRAME, self.hooks.Type.POST, IDENTIFIER):
                self.hooks.remove_hook(FRAME, self.hooks.Type.POST, IDENTIFIER)
            self.installed = False
        self.settings = None
        try:
            self._release()
        finally:
            if self.vehicle_id:
                vehicle_share.publish(vehicle_share.ZERO)
            self._forget()


def game_modules() -> tuple:
    import time
    from mods_base import get_pc
    from unrealsdk import hooks, logging
    from unrealsdk.unreal import WeakPointer
    return (hooks, get_pc, WeakPointer, lambda item: int(item._get_address()), time.perf_counter_ns,
            lambda message: logging.info(f"[Camera Runtime] {message}"))
