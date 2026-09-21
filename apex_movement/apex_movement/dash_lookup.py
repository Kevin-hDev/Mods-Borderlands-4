"""Knows which dash belongs to the character being played.

The first four characters share one dash, Move_Dash, at a fixed path. The two the up to date game added keep their
own: one of them plays Move_Dash_Corpohacker, filed under /Game/DLC/Harmonica/PlayerCharacters/CorpoHacker/, and
Move_Dash is then never loaded at all (2026-09-21). No field of the character points at it, so it is found by name,
two ways: the one dash the game has loaded, from the character's very first frame; and the dash the game is seen
playing, which settles it whenever the first way cannot, as when two characters share one game.

game.dash_asset asks this module first, and falls back on Move_Dash's own path.
"""

from itertools import islice
from typing import Any

import unrealsdk
from unrealsdk import unreal

# Only Move_Dash and Move_Dash_Corpohacker have ever been seen under that name (2026-09-21); the slide and the
# ground slam go by other names.
PREFIX = "Move_Dash"
CLASS_NAME = "OakControlledMove"
# A handful are loaded at a time (seven on 2026-09-21); the bound only guards the lookup.
MAX_MOVES = 64
# While no dash is loaded yet, looked for again once a second rather than at every frame.
SEARCH_NS = 1_000_000_000

_pointer: Any = None
_next_search_ns = 0


def _is_dash(move: Any) -> bool:
    return move is not None and str(getattr(move, "Name", "")).startswith(PREFIX)


def note(movement: Any) -> None:
    """Remembers the dash the game is playing right now, if it is one."""
    global _pointer
    move = movement.ControlledMoveReplicationData.ControlledMove
    if _is_dash(move):
        _pointer = unreal.WeakPointer(move)


def _only_loaded() -> Any:
    """The one dash the game has loaded, when there is exactly one; two or more say nothing on their own."""
    try:
        found = [move for move in islice(unrealsdk.find_all(CLASS_NAME, exact=False), MAX_MOVES) if _is_dash(move)]
    except Exception:
        # Expected while the game loads: looked up again a second later, and Move_Dash's own path is tried meanwhile.
        return None
    return found[0] if len(found) == 1 else None


def current(now_ns: int | None = None) -> Any:
    """The character's dash when known, else None. `now_ns` lets the caller that runs every frame search the loaded
    dashes, once a second at most."""
    global _pointer, _next_search_ns
    seen = _pointer() if _pointer is not None else None
    if seen is not None:
        return seen
    if now_ns is None or now_ns < _next_search_ns:
        return None
    _next_search_ns = now_ns + SEARCH_NS
    only = _only_loaded()
    if only is not None:
        _pointer = unreal.WeakPointer(only)
    return only


def forget() -> None:
    """Another character, perhaps another dash: looked for again at once."""
    global _pointer, _next_search_ns
    _pointer = None
    _next_search_ns = 0
