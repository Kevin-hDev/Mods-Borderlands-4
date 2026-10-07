"""Free Look on foot: the camera turns alone while the hunter keeps his direction, and his run if he was moving.

For the hold, the current camera mode's ViewTargetRotationUpdateMethod goes from FromCamera to Fixed, the value
Orbit uses, without changing mode (free_look_definitions.py); in first person the game's third person is laid first
(free_look_swap.py). A hunter moving at the press keeps running alone: the game's movement is set aside
(SetIgnoreMoveInput, a counter in Unreal, so each True is paired with exactly one False) and he is pushed along the
run, which left and right turn (free_look_run.py, free_look_inputs.py). At the release the camera is put back on the
view (SetBaseRotation) while Fixed still holds; the next frame the values go back and first person returns.
Verified in game with the probe, trials 7 to 16 (docs/third_person_fov/camera/2026-10-06-lock-view.md).
"""

import math
from typing import Any

from . import free_look_definitions as defs
from . import free_look_inputs, free_look_lookup, free_look_run, free_look_swap

HANDLED_MODES = (defs.THIRD_PERSON, defs.FIRST_PERSON)


def _rotator(sdk: Any, pitch: float, yaw: float) -> Any:
    return sdk.make_struct("Rotator", Pitch=pitch, Yaw=yaw, Roll=0.0)


class Foot:
    def __init__(self, sdk: Any, memory: Any, hooks: Any, log: Any) -> None:
        self.sdk, self.memory, self.log = sdk, memory, log
        self.guard = free_look_swap.Guard(hooks)
        self.modes = None
        self.refused = False
        self.written: tuple = ()
        self.laid = self.laid_manager = None
        self.run = None
        self.keys = free_look_inputs.MoveKeys((), (), ())
        self.returning = False

    def _available(self) -> bool:
        if self.modes is None and not self.refused:
            try:
                self.modes = free_look_lookup.find(self.sdk, self.memory)
            except LookupError as error:
                self.refused = True
                self.log(f"free look unavailable on foot: {error}")
        return self.modes is not None

    def begin(self, pc: Any) -> bool:
        """False when this camera or the game's memory does not allow Free Look now."""
        mode = str(pc.PlayerCameraManager.GetActorCameraMode(pc.Pawn))
        if mode not in HANDLED_MODES or not self._available():
            return False
        # Pressed again during the release's extra frame: the values still written are ours, not the game's.
        self.finish_return()
        if mode == defs.FIRST_PERSON:
            self.laid, self.laid_manager = free_look_swap.lay(pc), pc.PlayerCameraManager
            self.guard.install(pc)
        names = (defs.THIRD_PERSON, mode) if self.laid is not None else (mode,)
        for name in names:
            self._fix(name)
        if not self.written:
            self.finish_return()
            return False
        self._start_run(pc)
        return True

    def _fix(self, name: str) -> None:
        address = self.modes.addresses[name]
        if free_look_lookup.mode_at(self.memory, address, self.modes.shape) is None:
            self.log(f"free look: the {name} camera is no longer where it was found")
            return
        where = address + self.modes.shape.method
        if self.memory.read_int(where) == defs.FROM_CAMERA and self.memory.write_int(where, defs.FIXED):
            self.written += (where,)

    def _start_run(self, pc: Any) -> None:
        pawn = pc.Pawn
        velocity, pushed = pawn.GetVelocity(), pawn.GetLastMovementInputVector()
        self.run = free_look_run.start(math.hypot(float(velocity.X), float(velocity.Y)),
                                       math.hypot(float(pushed.X), float(pushed.Y)),
                                       float(pc.GetControlRotation().Yaw))
        if self.run is not None:
            self.keys = free_look_inputs.move_keys(pc.PlayerInput.EnhancedActionMappings)
            pc.SetIgnoreMoveInput(True)

    def frame(self, pc: Any, value: Any, step_s: float) -> None:
        """value(key name) is the game's analog state of that key."""
        if self.run is None:
            return
        before = self.run.yaw
        yaw = self.run.steer(free_look_inputs.side(value, self.keys), step_s)
        if yaw != before:
            pitch = float(pc.GetControlRotation().Pitch)
            pc.SetControlRotation(_rotator(self.sdk, pitch, yaw), bResetCamera=False)
        x, y = self.run.forward()
        pc.Pawn.AddMovementInput(WorldDirection=self.sdk.make_struct("Vector", X=x, Y=y, Z=0.0),
                                 ScaleValue=self.run.scale, bForce=True)

    def release(self, pc: Any) -> None:
        """Fixed stays one more frame, so the camera is moved before the game takes the view from it again."""
        self._end_run(pc)
        view = pc.GetControlRotation()
        pc.PlayerCameraManager.CameraModeState.SetBaseRotation(
            NewRotation=_rotator(self.sdk, float(view.Pitch), float(view.Yaw)))
        self.returning = True

    def _end_run(self, pc: Any) -> None:
        if self.run is not None:
            self.run = None
            pc.SetIgnoreMoveInput(False)

    def finish_return(self, stale: bool = False) -> None:
        """stale: the controller and its camera are gone; only the game's definitions, which stay, are put back."""
        written, self.written = self.written, ()
        for where in written:
            if self.memory.read_int(where) == defs.FIXED:
                self.memory.write_int(where, defs.FROM_CAMERA)
        self.guard.remove()
        laid, manager, self.laid, self.laid_manager = self.laid, self.laid_manager, None, None
        self.returning = False
        if laid is not None and not stale:
            free_look_swap.take_off(manager, laid)

    def abort(self, pc: Any) -> None:
        """Everything back at once: the mod stops, or the hunter took a vehicle. pc None: the player or the world
        changed, and nothing of the old one is touched."""
        try:
            if pc is not None:
                self._end_run(pc)
        finally:
            self.run = None
            self.finish_return(stale=pc is None)
