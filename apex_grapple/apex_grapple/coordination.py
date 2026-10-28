"""Read existing movement owners; never import or change another mod.

Polling before a rope writes is enough: a climb starting later in the same frame may use the
last impulse already acquired, then the next rope callback yields without writing again.
Only real wall climbing and the verified native mantle transfer ownership here. Dash, slide,
custom modes and wall proximity are not evidence that this rope should stop.
"""

import sys
from typing import Any

from . import report

# These are the two package names produced by the movement build, not display names or imports.
MOVEMENT_PACKAGES = ("apex_movement", "apex_wall_climb")
WALL_CLIMB = "wall climb"
MANTLE = "mantle"
UNAVAILABLE = "movement unavailable"
READ_FAILURE = "movement state could not be read; the grapple yields control"
MISSING_MANTLE = "mantle state is unavailable; mantle coordination cannot be checked"
_MISSING = object()


def _unavailable(key: str) -> str:
    # Fixed keys, bounded by report.error_once; engine details never enter a per-frame log.
    report.error_once(key, READ_FAILURE)
    return UNAVAILABLE


def _climb(character: Any, package_name: str) -> str | None:
    module = sys.modules.get(package_name)
    if module is None:
        return None
    try:
        # A package may exist while build_mod has not returned its root object yet.
        mod = getattr(module, "mod", None)
        if mod is None or not bool(getattr(mod, "is_enabled", False)):
            return None
        if module.game.character() != character:
            return None
        # The option can already be off while Movement's deferred stop still owns the arms.
        # Its rules, not that option or a wall trace, are the authority for actual climbing.
        if module.wall_climb._rules.start is not None:
            return WALL_CLIMB
    except Exception:
        return _unavailable(f"coordination:{package_name}")
    return None


def _mantle(character: Any) -> str | None:
    try:
        movement = character.CharacterMovement
        if movement is None:
            return _unavailable("coordination:movement_missing")
        mantle = getattr(movement, "ReplicatedMantleState", _MISSING)
        if mantle is _MISSING:
            # Missing capability differs from a broken read of an existing state. Older SDK
            # surfaces can lack it; report that limitation without claiming a native takeover.
            report.error_once("coordination:mantle_missing", MISSING_MANTLE)
            return None
        index = mantle.ActionIndex
        if not isinstance(index, int) or isinstance(index, bool):
            return _unavailable("coordination:mantle_invalid")
        if index >= 0:
            return MANTLE
    except Exception:
        return _unavailable("coordination:mantle_read")
    return None


def takeover(character: Any) -> str | None:
    """Return the owner/reason to yield, or None when no supported takeover is active."""
    for package_name in MOVEMENT_PACKAGES:
        reason = _climb(character, package_name)
        if reason is not None:
            return reason
    return _mantle(character)
