"""The game's stamina, the bar the dash and the glide spend, opened to the grapple.

Measured on 2026-09-22 (docs/investigations/apex_grapple/endurance/2026-09-22-reserve-du-dash.md): the reserve is
resourcepool'Vault_Power', full at 100, a dash costs 50, and the game refills it 3.2 s after the last
spend at about 25 a second. The player's character owns it, and it is reached only through
GameResourcePoolFunctionLibrary: the handle carries the type of the called function's own parameter,
never the movement definition's.

The cost is a share of the reserve rather than a number of units, so an upgrade that raises the
maximum raises the cost with it; the maximum is worked out from the value and the percentage the game
gives, since no function here reads it.

A reserve that cannot be read leaves the shot available by design. A readable empty reserve or
a failed debit refuses the shot before any movement or effect starts.
"""

from typing import Any

import unrealsdk

from . import report

LIBRARY = "GameResourcePoolFunctionLibrary"
READER = "GetResourcePoolValue"
PARAMETER = "InResource"
POOL = "Vault_Power"
READ_FAILURE = "Stamina could not be read; the grapple ignores it."
SPEND_FAILURE = "Stamina could not be spent; the shot was cancelled."
INSUFFICIENT = "no shot: not enough stamina"
# Kept between shots: the handle is a value, and building it costs two reflection lookups.
_handle: Any = None


def _library() -> Any:
    return unrealsdk.find_class(LIBRARY).ClassDefaultObject


def handle() -> Any:
    global _handle
    if _handle is None:
        kind = int(unrealsdk.find_class(LIBRARY)._find(READER)._find(PARAMETER).TypeHandle)
        # Reached through the module, as rope_audio reaches FGbxDefPtr: the type is not importable here.
        _handle = unrealsdk.unreal.FGameDataHandle(kind, POOL)
    return _handle


def forget() -> None:
    """Drops the value handle so the next read resolves its type again."""
    global _handle
    _handle = None


def reserve(character: Any) -> tuple[float, float] | None:
    """(what is left, the maximum), or None when the game does not answer."""
    try:
        left = float(_library().GetResourcePoolValue(character, handle()))
        share = float(_library().GetResourcePoolPercent(character, handle()))
    except Exception:
        forget()
        report.error_once("stamina:read", READ_FAILURE)
        return None
    # No previous character's maximum is needed: an empty reserve is refused directly.
    return left, max(left / share, left) if share > 0.0 else left


def try_spend(character: Any, percent: float) -> bool:
    """Allow a validated shot only after one snapshot and its successful debit."""
    if percent <= 0.0:
        return True
    found = reserve(character)
    if found is None:
        return True  # Unreadable resource remains permissive, as explicitly requested.
    left, maximum = found
    amount = maximum * percent / 100.0
    if left <= 0.0 or left < amount:
        # Caller keeps the key: an empty reserve must not fall through to a punch.
        report.note(INSUFFICIENT)
        return False
    try:
        _library().AdjustResourcePoolValue(character, handle(), -amount)
    except Exception:
        forget()
        report.error_once("stamina:spend", SPEND_FAILURE)
        return False
    return True
