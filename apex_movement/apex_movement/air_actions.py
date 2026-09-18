"""Starts what a blocked crouch asks for, and releases each request once the game is done with it.

All three calls were verified in game in sessions 4 and 5 (2026-09-16): SetWantsToDash starts a dash 8 to 9 ms later
in the asked direction, SetWantsToSlide a full slide at any landing speed 8 to 13 ms after landing, AttemptGroundSlam a
slam 7 ms later. The game keeps its own rules on top, such as the dash recharge.
"""

import math
from typing import Any

from unrealsdk import unreal

from . import game, report, settings

# The game only knows four dash directions, counted from the camera (BL4 SuperDash, confirmed in session 5).
FORWARD, LEFT, BACK, RIGHT = 0, 1, 2, 3
# Below this the stick counts as at rest and the dash goes forward. Carried over from the probe's air dash
# (apex_probe/snapshots.py), where it was chosen, not measured.
MIN_STICK = 0.2
# A native tap dashed within about 10 ms of the release; 300 ms is BL4 SuperDash's own timeout.
DASH_WATCH_NS = 300_000_000
# A dash request released as soon as the dash started stopped the dash one frame later: 18 mod dashes lasted 7 to 10 ms
# against 324 ms for the game's own (2026-09-17, 00:59-01:01). The request is now kept until the dash ends; this is
# only a safety net, above the 737 ms of a dash at 300 %.
DASH_HOLD_MAX_NS = 1_000_000_000
# Mod slides started 8 to 13 ms after the call; past 400 ms the call did nothing.
SLIDE_WATCH_NS = 400_000_000
# Safety net only. With 1.6 s, five landing slides ended at 1600-1608 ms while still fast (0.3.0 test): releasing the
# request ends the slide (verified on 2026-09-17), so it must outlast the longest slide slide_physics allows.
SLIDE_MAX_NS = int((settings.LONGEST_SLIDE_S + 5.0) * 1_000_000_000)

_dash: dict[str, Any] = {}
_slide: dict[str, Any] = {}
# When a tap comes during a dash: the frame from which the next dash is asked.
_queued_ns: int | None = None
# The character the watched requests were asked on, held weakly: forget() runs after a level load, when it may be
# destroyed already. An SDK object is a bare pointer, so calling a destroyed one is undefined, where a WeakPointer
# answers None (the installed SDK's stubs; not tried in game).
_asked_on: Any = None


def dash_direction(character: Any) -> int:
    x, y = game.stick_direction(character)
    view_yaw = game.view_yaw(character)
    if math.hypot(x, y) < MIN_STICK or view_yaw is None:
        return FORWARD
    yaw = math.radians(view_yaw)
    # Unreal is left-handed: yaw 0 looks along +X, and +Y is to the right.
    forward = x * math.cos(yaw) + y * math.sin(yaw)
    right = -x * math.sin(yaw) + y * math.cos(yaw)
    if abs(forward) >= abs(right):
        return FORWARD if forward >= 0 else BACK
    return RIGHT if right >= 0 else LEFT


def _move_text(movement: Any) -> str:
    data = movement.ControlledMoveReplicationData
    return f"{data.ControlledMove!r}|{data.PackedDirection!r}"


def _asked(character: Any) -> None:
    global _asked_on
    _asked_on = unreal.WeakPointer(character)


def _ask_dash(character: Any, now_ns: int) -> None:
    global _queued_ns
    _queued_ns = None
    chosen = dash_direction(character)
    before = _move_text(character.CharacterMovement)
    character.SetWantsToDash(True, chosen)
    _asked(character)
    _dash.update(start_ns=now_ns, direction=chosen, before=before, during=None)
    report.note(f"air dash asked direction={chosen}")


def _release_dash(character: Any) -> None:
    character.SetWantsToDash(False, _dash["direction"])
    _dash.clear()


def _release_slide(character: Any) -> None:
    character.SetWantsToSlide(False)
    _slide.clear()


def start_dash(character: Any, now_ns: int) -> None:
    global _queued_ns
    if not _dash:
        _ask_dash(character, now_ns)
        return
    if _dash["during"] is None:
        return
    # Two dashes chain 146 to 240 ms apart in the game: a tap during a dash ends it and asks the next one a frame
    # later, so the game sees the request drop before it comes back.
    report.note(f"air dash chained after_ms={(now_ns - _dash['start_ns']) // 1_000_000}")
    _release_dash(character)
    _queued_ns = now_ns + 1


def start_slide(character: Any, now_ns: int, speed_in: float, minimum: float) -> None:
    if _slide:
        report.note(f"landing slide not asked speed_in={speed_in:.0f}: the last one is still watched")
        return
    character.SetWantsToSlide(True)
    _asked(character)
    _slide.update(start_ns=now_ns, started=False)
    report.note(f"landing slide asked speed_in={speed_in:.0f} min={minimum:.0f}")


def slam(character: Any) -> None:
    report.note(f"air slam asked started={character.AttemptGroundSlam()}")


def _update_dash(character: Any, now_ns: int) -> None:
    age_ns = now_ns - _dash["start_ns"]
    current = _move_text(character.CharacterMovement)
    if _dash["during"] is not None:
        if current == _dash["during"] and age_ns < DASH_HOLD_MAX_NS:
            return
        report.note(f"air dash ended after_ms={age_ns // 1_000_000}")
        _release_dash(character)
        return
    started = "Move_Dash" in current and current != _dash["before"]
    if started:
        _dash["during"] = current
        report.note(f"air dash started after_ms={age_ns // 1_000_000}")
        return
    if age_ns < DASH_WATCH_NS:
        return
    # Not started is normal while the dash reserve is empty: two dashes, then up to 7.8 s to get both back (2026-09-16).
    report.note(f"air dash not started after_ms={age_ns // 1_000_000}")
    _release_dash(character)


def _update_slide(character: Any, now_ns: int) -> None:
    age_ns = now_ns - _slide["start_ns"]
    sliding = game.is_sliding(character.CharacterMovement)
    if sliding and not _slide["started"]:
        _slide["started"] = True
        report.note(f"landing slide started after_ms={age_ns // 1_000_000}")
    ended = _slide["started"] and (not sliding or age_ns >= SLIDE_MAX_NS)
    if not ended and (_slide["started"] or age_ns < SLIDE_WATCH_NS):
        return
    if not _slide["started"]:
        report.note(f"landing slide not started within_ms={SLIDE_WATCH_NS // 1_000_000}")
    # Released only at the end: left on, the flag stretched a slide from 1357 to 1603 ms (session 4).
    _release_slide(character)


def update(character: Any, now_ns: int) -> None:
    if _dash:
        _update_dash(character, now_ns)
    elif _queued_ns is not None and now_ns >= _queued_ns:
        _ask_dash(character, now_ns)
    if _slide:
        _update_slide(character, now_ns)


def _release(character: Any) -> None:
    if _dash:
        _release_dash(character)
    if _slide:
        _release_slide(character)


def forget() -> None:
    """Releases what is still asked on the character it was asked on, when that one still exists, then drops the
    watches: the character changed, and the new one never saw these requests."""
    global _queued_ns, _asked_on
    kept = _asked_on() if _asked_on is not None and (_dash or _slide) else None
    if kept is not None:
        try:
            _release(kept)
        except Exception as exc:
            # Called at a level change for every movement: raising here would stop the others' reset too. A request
            # the old character cannot drop goes away with it.
            report.error_once("air_actions:forget", f"air request not released on the old character: {exc!r}")
    _dash.clear()
    _slide.clear()
    _queued_ns = _asked_on = None


def stop(character: Any) -> None:
    if character is not None:
        _release(character)
    forget()
