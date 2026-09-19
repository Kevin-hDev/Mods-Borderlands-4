"""Runs the mod once per frame while the player drives: holds the vehicle, keeps its values, grips it.

The hook is only a clock, as in Apex Movement and the probes: any animation update ticks it, and several update each
frame, so a tick closer than MIN_STEP_NS to the last is the same frame seen again. At the wheel the controller has no
character (session 1, 2026-09-18), so no single animation could be trusted to keep running.
A part that raises, the values or the grip, stops alone until the next vehicle and is reported once: one broken part
must not take the other down (spec section 3.4).
"""

import time
from typing import Any

from mods_base import get_pc, hook
from unrealsdk.hooks import Type

from . import grip, report, seat, settings, tuning

HOOK_PATH = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
MS = 1_000_000
MIN_STEP_NS = 3 * MS
# Twice a second: a slider moved in the menu, or a value the game rewrote, is followed within half a second.
CHECK_NS = 500 * MS
VALUES = "values"
GRIP = "grip"

_tuning = tuning.Tuning()
_grip = grip.Grip(0)
_failed: set[str] = set()
_last_ns = 0
_next_check_ns = 0


def _say(lines: list[str]) -> None:
    for line in lines:
        report.note(line)


def _errors(lines: list[str]) -> None:
    for line in lines:
        report.error_once(line, line)


def _fail(part: str, exc: Exception) -> None:
    _failed.add(part)
    report.error_once(part, f"{part} stopped until the next vehicle after an error: {exc!r}")


def _switch(vehicle: Any, now_ns: int) -> None:
    """The player got in, out, or into another vehicle: the values held go back first."""
    global _grip, _next_check_ns
    _failed.clear()
    _errors(_tuning.put_back())
    if vehicle is None:
        report.note("left the vehicle, game values back")
        return
    try:
        _say(_tuning.take(vehicle))
    except Exception as exc:
        _fail(VALUES, exc)
    _grip = grip.Grip(now_ns)
    _next_check_ns = now_ns


def on_frame(now_ns: int) -> None:
    global _last_ns, _next_check_ns
    if now_ns - _last_ns < MIN_STEP_NS:
        return
    _last_ns = now_ns
    vehicle = seat.driven_vehicle(get_pc(possibly_loading=True))
    # A vehicle destroyed under its driver reads None like no vehicle at all: holds() still sees its driver's values.
    if vehicle != _tuning.vehicle() or (vehicle is None and _tuning.holds()):
        _switch(vehicle, now_ns)
    if vehicle is None:
        return
    for line in settings.keep_in_bounds():
        report.warning(line)
    if now_ns >= _next_check_ns and VALUES not in _failed:
        _next_check_ns = now_ns + CHECK_NS
        try:
            _say(_tuning.update(settings.factors()))
        except Exception as exc:
            _fail(VALUES, exc)
    if settings.grip.value and GRIP not in _failed:
        try:
            _say(_grip.step(now_ns, vehicle, settings.loss_per_degree()))
        except Exception as exc:
            _fail(GRIP, exc)


def stop_all() -> list[str]:
    """Puts every value back; returns one line per value that could not be."""
    global _last_ns
    _failed.clear()
    _last_ns = 0
    return _tuning.put_back()


# The identifier carries the package's name, as Apex Movement's does on this same function (apex_movement:frame): two
# identifiers never replace each other, so both mods run each frame (spec section 4).
@hook(HOOK_PATH, Type.POST, hook_identifier=f"{__package__}:frame")
def tick(_obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    try:
        on_frame(time.perf_counter_ns())
    except Exception as exc:
        # Outside the parts, such as the controller lookup: the frame is skipped, the game goes on.
        report.error_once("frame", f"a frame was skipped after an error: {exc!r}")
