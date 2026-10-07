"""Free Look at the wheel: the vehicle keeps its direction and its throttle while the camera turns alone.

The game steers a vehicle toward the view, so the view is put back on the locked direction each frame and the
mouse's turn goes to the camera alone through CameraModeState.BaseRotationOffset (free_look_angles.py), which the
game sets back each frame. A vehicle moving at the press keeps its throttle without the key until the brake, and goes
straight (Kevin, 2026-10-07). At the release the view and the camera are both put back on the locked direction: the
view alone was taken back from the still turned camera the next frame, and the vehicle turned (trials 14 and 16).
Vehicle Driving writes the camera's place, never its rotation, and ran during these trials. Verified in game with the
probe, trials 3, 13, 17 and 18 (docs/third_person_fov/camera/2026-10-06-lock-view.md).
"""

import math
from typing import Any

from . import free_look_inputs, free_look_run
from .free_look_angles import Look

THROTTLE_KEPT = 0.05


def _rotator(sdk: Any, pitch: float, yaw: float) -> Any:
    return sdk.make_struct("Rotator", Pitch=pitch, Yaw=yaw, Roll=0.0)


def _write_offset(manager: Any, pitch: float, yaw: float) -> None:
    offset = manager.CameraModeState.BaseRotationOffset
    offset.Pitch, offset.Yaw, offset.Roll = pitch, yaw, 0.0


class Wheel:
    def __init__(self, sdk: Any, log: Any) -> None:
        self.sdk, self.log = sdk, log
        self.look = None
        self.manager = None
        self.throttle = 0.0
        self.keys = free_look_inputs.MoveKeys((), (), ())
        self.throttle_missing_told = False

    def begin(self, pc: Any) -> bool:
        vehicle = pc.Pawn
        view = pc.GetControlRotation()
        self.look = Look(float(view.Pitch), float(view.Yaw))
        self.manager = pc.PlayerCameraManager
        velocity = vehicle.GetVelocity()
        movement = vehicle.OakVehicleMovement
        moving = math.hypot(float(velocity.X), float(velocity.Y)) >= free_look_run.MOVING_SPEED
        self.throttle = float(movement.RawThrottleInput) if moving else 0.0
        if self.throttle < THROTTLE_KEPT:
            self.throttle = 0.0
        elif not hasattr(movement, "SetThrottleInput"):
            self.throttle = 0.0
            if not self.throttle_missing_told:
                self.throttle_missing_told = True
                self.log("free look: this vehicle has no throttle to keep")
        self.keys = free_look_inputs.move_keys(pc.PlayerInput.EnhancedActionMappings)
        return True

    def frame(self, pc: Any, value: Any) -> None:
        """value(key name) is the game's analog state of that key."""
        if self.throttle > 0.0 and free_look_inputs.brakes(value, self.keys):
            self.throttle = 0.0
        if self.throttle > 0.0:
            pc.Pawn.OakVehicleMovement.SetThrottleInput(self.throttle)
        view = pc.GetControlRotation()
        pitch, yaw = self.look.absorb(float(view.Pitch), float(view.Yaw))
        pc.SetControlRotation(_rotator(self.sdk, pitch, yaw), bResetCamera=False)
        _write_offset(self.manager, self.look.pitch, self.look.yaw)

    def release(self, pc: Any) -> None:
        pitch, yaw = self.look.anchor
        pc.SetControlRotation(_rotator(self.sdk, pitch, yaw), bResetCamera=False)
        self.manager.CameraModeState.SetBaseRotation(NewRotation=_rotator(self.sdk, pitch, yaw))
        self.abort()

    def abort(self, stale: bool = False) -> None:
        """stale: the camera is gone, nothing of it is touched."""
        manager, self.manager, self.look, self.throttle = self.manager, None, None, 0.0
        if manager is not None and not stale:
            _write_offset(manager, 0.0, 0.0)
