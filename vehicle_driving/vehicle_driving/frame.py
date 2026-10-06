"""Runs the mod once per frame while the player drives: holds the vehicle, keeps its values, grips it, pushes it in the
air and places the camera of the chosen view.

The hook is only a clock, as in Apex Movement and the probes: any animation update ticks it, and several update each
frame, so a tick closer than MIN_STEP_NS to the last is the same frame seen again. At the wheel the controller has no
character (session 1, 2026-09-18), so no single animation could be trusted to keep running.
A part that raises, the values, the grip, the push or the camera, stops alone until the next vehicle, and each kind of error is
reported once: one broken part must not take the others down (spec section 3.4).
"""

import time
from typing import Any

from mods_base import get_pc, hook
from unrealsdk.hooks import Type

from . import air_push, camera_view, grip, report, seat, settings, tuning

HOOK_PATH = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
MS = 1_000_000
MIN_STEP_NS = 3 * MS
# Twice a second: a slider moved in the menu, or a value the game rewrote, is followed within half a second.
CHECK_NS = 500 * MS
VALUES = "values"
GRIP = "grip"
AIR = "air push"
CAMERA = "camera"

_tuning = tuning.Tuning()
_grip = grip.Grip(0)
_air = air_push.AirPush(0)
_camera = camera_view.CameraView()
# Read at each check with the other sliders, once in bounds; the view itself is read every frame, so a key press shows
# at the next frame.
_custom = (0.0, 0.0, 0.0)
_view = settings.DEFAULT_VIEW
_failed: set[str] = set()
_last_ns = 0
_next_check_ns = 0
# Set at each check, the first one coming with the vehicle itself (_switch), before the grip's first frame.
_loss = 0.0
# Set at each check too: a push typed past its top between two checks never reaches the vehicle.
_push = 0.0


def _say(lines: list[str]) -> None:
    for line in lines:
        report.note(line)


def _errors(lines: list[str]) -> None:
    for line in lines:
        report.error_once(line, line)


def _fail(part: str, exc: Exception) -> None:
    _failed.add(part)
    # Keyed by the kind of error, not the part alone: another failure on a later vehicle must still reach the log.
    report.error_once(f"{part}:{type(exc).__name__}", f"{part} stopped until the next vehicle after an error: {exc!r}")


def _switch(vehicle: Any, now_ns: int) -> None:
    """The player got in, out, or into another vehicle: the values held go back first."""
    global _grip, _air, _next_check_ns
    _failed.clear()
    _errors(_camera.release())
    _errors(_tuning.put_back())
    if vehicle is None:
        report.note("left the vehicle, game values back")
        return
    try:
        _say(_tuning.take(vehicle))
    except Exception as exc:
        _fail(VALUES, exc)
    _grip = grip.Grip(now_ns)
    _air = air_push.AirPush(now_ns)
    _next_check_ns = now_ns


def on_frame(now_ns: int) -> None:
    global _last_ns, _next_check_ns, _loss, _push, _custom, _view
    if now_ns - _last_ns < MIN_STEP_NS:
        return
    _last_ns = now_ns
    pc = get_pc(possibly_loading=True)
    vehicle = seat.driven_vehicle(pc)
    # A vehicle destroyed under its driver reads None like no vehicle at all: holds() still sees its driver's values.
    if vehicle != _tuning.vehicle() or (vehicle is None and _tuning.holds()):
        _switch(vehicle, now_ns)
    if vehicle is None:
        return
    if now_ns >= _next_check_ns:
        _next_check_ns = now_ns + CHECK_NS
        for line in settings.keep_in_bounds():
            report.warning(line)
        # Read here, once in bounds: a loss typed past its top between two checks never reaches the grip.
        _loss = settings.loss_per_degree()
        _push = settings.push_strength()
        _custom = settings.custom_offset()
        if VALUES not in _failed:
            try:
                _say(_tuning.update(settings.factors()))
            except Exception as exc:
                _fail(VALUES, exc)
    pushed = False
    if AIR not in _failed:
        try:
            pushed, lines = _air.step(now_ns, vehicle, _push)
            _say(lines)
        except Exception as exc:
            _fail(AIR, exc)
    # One part sets the vehicle's speed in a frame: the grip's write would wipe the push out (spec section 3.6).
    if not settings.grip.value or pushed:
        _grip.rest(now_ns)
    elif GRIP not in _failed:
        try:
            _say(_grip.step(now_ns, vehicle, _loss))
        except Exception as exc:
            _fail(GRIP, exc)
    view = settings.current_view()
    if view != _view:
        _view = view
        report.note(f"camera view {view}")
    if CAMERA not in _failed:
        try:
            _say(_camera.step(now_ns, vehicle, getattr(pc, "PlayerCameraManager", None), view, _custom))
        except Exception as exc:
            _fail(CAMERA, exc)
            _errors(_camera.release())


def stop_all() -> list[str]:
    """Puts every value back, the camera's offset too; returns one line per value that could not be."""
    global _last_ns
    _failed.clear()
    _last_ns = 0
    return _tuning.put_back() + _camera.release()


# The identifier carries the package's name, as Apex Movement's does on this same function (apex_movement:frame): two
# identifiers never replace each other, so both mods run each frame (spec section 4).
@hook(HOOK_PATH, Type.POST, hook_identifier=f"{__package__}:frame")
def tick(_obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    try:
        on_frame(time.perf_counter_ns())
    except Exception as exc:
        # Outside the parts, such as the controller lookup: the frame is skipped, the game goes on.
        report.error_once(f"frame:{type(exc).__name__}", f"a frame was skipped after an error: {exc!r}")
