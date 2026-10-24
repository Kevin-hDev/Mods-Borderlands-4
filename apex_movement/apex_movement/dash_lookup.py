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
# Two dashes or more loaded tell nothing a new search could settle; the dash played settles it (note). A search walks
# every object of the game, about 10 ms in one frame (It Follows trial 38), so it is made again only in case one of
# them is unloaded meanwhile (2026-10-24).
AMBIGUOUS_SEARCH_NS = 10_000_000_000

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


def _loaded() -> list[Any]:
    """The dashes the game has loaded; only exactly one says whose it is."""
    try:
        return [move for move in islice(unrealsdk.find_all(CLASS_NAME, exact=False), MAX_MOVES) if _is_dash(move)]
    except Exception:
        # Expected while the game loads: looked up again a second later, and Move_Dash's own path is tried meanwhile.
        return []


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
    found = _loaded()
    if len(found) != 1:
        if found:
            _next_search_ns = now_ns + AMBIGUOUS_SEARCH_NS
        return None
    _pointer = unreal.WeakPointer(found[0])
    return found[0]


def forget() -> None:
    """Another character, perhaps another dash: looked for again at once."""
    global _pointer, _next_search_ns
    _pointer = None
    _next_search_ns = 0
