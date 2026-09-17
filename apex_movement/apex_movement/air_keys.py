"""Decides what a crouch press does in the air, before the game sees it (spec, section 2.3).

Ported from probe 0.5.0, whose whole rule Kevin played in session 5 (2026-09-16) with no felt difference but the one
wanted: a crouch held in the air no longer slams. On the ground every press reaches the game unchanged.
This module only decides; air_crouch turns the requests into game calls.
"""

from typing import Any

from . import report

# Kevin's "same time" presses in sessions 3 and 4 came 0 to 30 ms apart, in either order.
COMBO_WINDOW_NS = 80_000_000
# The game's hold trigger fires at 0.2 s; its native dash came from releases at 96 to 110 ms.
TAP_MAX_NS = 200_000_000
# The game's own slam starts 0.2 s after crouch; the double jump also needs that time to give the height.
SLAM_DELAY_NS = 200_000_000
# Bounded: requests are drained every frame, so more than this means the frame loop stopped; new ones are dropped.
MAX_REQUESTS = 20

# A hold released after this long is logged: it tells a chain the player let go of from one the mod dropped.
LONG_HOLD_NS = 500_000_000
# One entry per crouch key held, so a handful at most.
_held: dict[str, dict[str, Any]] = {}
# Crouch keys pressed on the ground and still down. A slide jump keeps crouch down from the ground: without this, only a
# press made in the air slid at landing, and chained jump slides stopped whenever the hold began on the ground (0.8.4,
# 2026-09-17: 16 slides ended by a jump without a landing slide, none of them after a press in the air). Presses passed
# to the game in the air for its slam are not kept: a slam must not slide at landing.
_ground_held: dict[str, int] = {}
_last_jump_ns: int | None = None
_requests: list[tuple[str, int]] = []


def reset() -> None:
    global _last_jump_ns
    _held.clear()
    _ground_held.clear()
    _requests.clear()
    _last_jump_ns = None


def _request(kind: str, due_ns: int) -> None:
    if len(_requests) < MAX_REQUESTS:
        _requests.append((kind, due_ns))


def crouch_event(key: str, event: str, now_ns: int, in_air: bool) -> bool:
    """True when the event must not reach the game."""
    if event != "IE_Pressed":
        if event == "IE_Released":
            _log_long_release(key, now_ns, in_air)
            _ground_held.pop(key, None)
        # The release and repeats of a blocked press are blocked too, so the game never sees half of a press.
        if key not in _held:
            return False
        if event == "IE_Released":
            press = _held.pop(key)
            if not press["combo"] and in_air and now_ns - press["press_ns"] < TAP_MAX_NS:
                _request("dash", now_ns)
        return True
    if not in_air:
        _ground_held[key] = now_ns
        return False
    if _last_jump_ns is not None and now_ns - _last_jump_ns <= COMBO_WINDOW_NS:
        # Jump then crouch: the game slams on its own from this press (session 5), so it goes through.
        report.note(f"air crouch passed to the game: jump {(now_ns - _last_jump_ns) // 1_000_000} ms before")
        return False
    _held[key] = {"press_ns": now_ns, "combo": False}
    report.note(f"air crouch blocked key={key}")
    return True


def _log_long_release(key: str, now_ns: int, in_air: bool) -> None:
    pressed_ns = _ground_held.get(key, _held[key]["press_ns"] if key in _held else None)
    if pressed_ns is not None and now_ns - pressed_ns >= LONG_HOLD_NS:
        report.note(f"crouch released key={key} after_ms={(now_ns - pressed_ns) // 1_000_000} in_air={in_air}")


def jump_event(event: str, now_ns: int) -> None:
    """Jump always reaches the game; right after a blocked crouch it turns that crouch into a ground slam."""
    global _last_jump_ns
    if event != "IE_Pressed":
        return
    _last_jump_ns = now_ns
    for press in _held.values():
        if not press["combo"] and now_ns - press["press_ns"] <= COMBO_WINDOW_NS:
            press["combo"] = True
            _request("slam", now_ns + SLAM_DELAY_NS)
            report.note(f"air crouch then jump {(now_ns - press['press_ns']) // 1_000_000} ms later: slam asked")


def is_held() -> bool:
    """A crouch is still held down: pressed on the ground, or blocked in the air and not part of a combination."""
    return bool(_ground_held) or any(not press["combo"] for press in _held.values())


def due_requests(now_ns: int) -> list[str]:
    due = [kind for kind, at_ns in _requests if at_ns <= now_ns]
    _requests[:] = [(kind, at_ns) for kind, at_ns in _requests if at_ns > now_ns]
    return due
