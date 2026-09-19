"""Runs Omni Sprint twice a second: finds the movement definition of the character played and keeps it open.

The hook is only a clock, as in Apex Movement and Vehicle Driving: any animation update ticks it, several times a
frame, so a tick before the next check does nothing. Loading a game makes a new character, while a fast travel keeps
it (2026-09-19, verified in game), and each character has its own definition, so a new movement component means a
new search. A definition not found yet is searched again later; one never found, or found but not opened, is
reported once and left alone until the character changes.
"""

import time
from typing import Any

from mods_base import get_pc, hook
from unrealsdk.hooks import Type

from . import definition, limit, report

HOOK_PATH = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
MS = 1_000_000
# Twice a second: a sprint started just after a zone change is opened within half a second.
CHECK_NS = 500 * MS
# While a game loads, the character exists before its definition can be found: on 2026-09-19 (13:39:40) the first
# search missed, and the same character's search found it two minutes later. So a miss is searched again, waiting
# twice as long each time up to RETRY_MAX_NS, and given up after MAX_TRIES, about two minutes in all.
RETRY_FIRST_NS = 500 * MS
RETRY_MAX_NS = 16_000 * MS
MAX_TRIES = 12

_shape: definition.Layout | None = None
_shape_read = False
_component = 0
_definition = 0
_tries = 0
_next_search_ns = 0
_given_up = False
_next_ns = 0


def reset() -> None:
    global _shape, _shape_read, _next_ns
    _shape, _shape_read, _next_ns = None, False, 0
    _follow(0, 0)


def _follow(component: int, now_ns: int) -> None:
    global _component, _definition, _tries, _next_search_ns, _given_up
    _component, _definition, _tries, _next_search_ns, _given_up = component, 0, 0, now_ns, False


def _layout() -> definition.Layout | None:
    # Read once per switch-on: the type is the game's own and does not change while it runs.
    global _shape, _shape_read
    if not _shape_read:
        _shape_read = True
        _shape = definition.layout()
        if _shape is None:
            report.error_once("layout", f"the game's {definition.TYPE_NAME} type has changed: nothing written")
    return _shape


def _component_address() -> int:
    """The address of the played character's movement component, 0 without a character (title screen, wheel)."""
    pc = get_pc(possibly_loading=True)
    character = getattr(pc, "OakCharacter", None) if pc is not None else None
    movement = getattr(character, "CharacterMovement", None) if character is not None else None
    return int(movement._get_address()) if movement is not None else 0


def _look(shape: definition.Layout, now_ns: int) -> None:
    global _definition, _tries, _next_search_ns, _given_up
    found = definition.find(_component, shape)
    _tries += 1
    if found is not None:
        _definition = found.address
        after = f", after {_tries} searches" if _tries > 1 else ""
        report.note(f"movement definition found at {found.address:#x}, movement component +{found.slot:#x}{after}")
        return
    if _tries >= MAX_TRIES:
        _given_up = True
        report.warning_once(
            f"none:{_component:#x}",
            f"no movement definition found for this character after {_tries} searches: nothing written, sprint as usual",
        )
        return
    _next_search_ns = now_ns + min(RETRY_FIRST_NS * 2 ** (_tries - 1), RETRY_MAX_NS)


def on_frame(now_ns: int) -> None:
    global _next_ns, _component, _given_up
    if now_ns < _next_ns:
        return
    _next_ns = now_ns + CHECK_NS
    shape = _layout()
    component = _component_address() if shape is not None else 0
    if component == 0:
        return
    if component != _component:
        _follow(component, now_ns)
    if _given_up:
        return
    if _definition == 0:
        if now_ns >= _next_search_ns:
            _look(shape, now_ns)
        if _definition == 0:
            return
    try:
        line = limit.hold(_definition, shape)
    except limit.Lost as exc:
        report.note(f"{exc}: looking for it again")
        _component = 0
        return
    except limit.NotOpened as exc:
        report.error_once(str(exc), str(exc))
        _given_up = True
        return
    if line is not None:
        report.note(line)


def stop() -> tuple[int, int]:
    """Puts back every limit opened: (put back, left alone)."""
    shape = _shape
    reset()
    return limit.put_back(shape)


# The identifier carries the package's name, as Apex Movement's and Vehicle Driving's do on this same function: two
# identifiers never replace each other, so the three mods run each frame.
@hook(HOOK_PATH, Type.POST, hook_identifier=f"{__package__}:frame")
def tick(_obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    try:
        on_frame(time.perf_counter_ns())
    except Exception as exc:
        report.error_once("frame", f"a check was skipped after an error: {exc!r}")
