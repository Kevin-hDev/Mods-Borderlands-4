"""Owns every game value Apex Movement writes: keeps the game's own value at the first write and puts it back.

Design decision 4: the mod is the only authority on the values it writes, and restores all of them when it stops.
Character values die with the character on a level change, so they are forgotten rather than written back into a
destroyed object; asset values (Move_Slide, jump goals) outlive characters and are always restored, unless the game
has unloaded the asset: it then loads it again from its files, with its own values.
"""

import enum
from typing import Any, Callable, Iterable

CHARACTER = "character"
ASSET = "asset"

# The tolerances live here, in a module every separate file carries: the dash, the slides and the ground speeds compare
# with them, and ship as separate files that may not import one another.
# Game floats are 32-bit: a value under about 1600 read back differs from the one written by less than this, so a
# difference this small is rounding, and a value this small is zero.
TOLERANCE = 1e-4
# Speeds closer than this, in game units a second, are one speed: the speed sliders move by whole units, about 0.8 on
# the slide's speed constant (a speed divided by 1.27), while the game's rounding stays far below.
SPEED_TOLERANCE = 0.5

_entries: dict[str, dict[str, Any]] = {}


class Unloaded(Exception):
    """Raised by a put whose asset the game has unloaded: Move_Slide at the title screen (2026-09-19)."""


def loaded(asset: Any) -> Any:
    """The asset a put writes into, as game.slide_asset() gives it; raises Unloaded when that is None."""
    if asset is None:
        raise Unloaded()
    return asset


def claim(key: str, scope: str, get: Callable[[], Any], put: Callable[[Any], None]) -> None:
    """Takes a value the mod holds without writing it again, the game already holding what the movement wants.

    A value the mod does not own is a value it never gives back. Until 2026-09-20 a movement simply returned here,
    so a value whose record had been lost stayed in the game for good: the movement never wrote it again, since it
    already read right, and the mod had nothing left to put back.
    """
    if key in _entries:
        _entries[key]["get"], _entries[key]["put"] = get, put
        _entries[key].pop("unloaded", None)
        return
    _entries[key] = {"scope": scope, "get": get, "put": put, "original": get()}


def write(key: str, scope: str, get: Callable[[], Any], put: Callable[[Any], None], value: Any) -> None:
    claim(key, scope, get, put)
    put(value)
    _entries[key]["written"] = value


def adopt_game_value(key: str, tolerance: float) -> bool:
    """Takes the value the game holds as its own when it has computed one over the mod's since the last write.

    For values the game computes again by itself, such as the speed scale when aiming: put back as read at the first
    write, the walk key's release left the aiming scale on a character no longer aiming (audit, 2026-09-25).
    """
    entry = _entries.get(key)
    if entry is None or "written" not in entry:
        return False
    current = entry["get"]()
    if abs(current - entry["written"]) <= tolerance:
        return False
    entry["original"] = current
    return True


def is_owned(key: str) -> bool:
    return key in _entries


def original(key: str) -> Any:
    return _entries[key]["original"]


def _checkable(value: Any) -> bool:
    """Whether a value read back can be compared without guessing: numbers, flags, enums and tuples of those.

    A curve or a game struct is left unchecked rather than called wrong on a comparison the SDK does not define.
    """
    if isinstance(value, tuple):
        return bool(value) and all(_checkable(item) for item in value)
    return isinstance(value, (bool, int, float, enum.Enum))


def _left_behind(key: str, entry: dict[str, Any]) -> str | None:
    """What the game still holds after a put that raised nothing, when that is not what was put back.

    A put that changes nothing raises nothing either: on 2026-09-20 the mod announced every value restored while
    the game kept the gravity it had been given.
    """
    original = entry["original"]
    if not _checkable(original):
        return None
    try:
        current = entry["get"]()
    except Exception as exc:
        return f"{key} was put back but cannot be read again: {exc!r}"
    return None if current == original else f"{key} still reads {current!r} after putting {original!r} back"


def restore(key: str) -> None:
    entry = _entries.get(key)
    if entry is None:
        return
    try:
        entry["put"](entry["original"])
    except Unloaded:
        # No failure: nothing holds the mod's value any more. Kept all the same, so that a write after the game loads
        # the asset again keeps the game's value it already has; written as ten false errors until 2026-09-19.
        entry["unloaded"] = True
        return
    left = _left_behind(key, entry)
    if left is not None:
        # Kept owned, like a put that raised: the game's value is still here for the next try, and the mod says so
        # instead of announcing a value it never put back.
        raise RuntimeError(left)
    # Forgotten only once put back: after a put that fails, the game's value is still here for the next try instead of
    # lost for good.
    del _entries[key]


def restore_each(keys: Iterable[str]) -> list[str]:
    """Tries every key even after one fails; returns one line per value that could not be put back and stays owned."""
    failures: list[str] = []
    for key in keys:
        try:
            restore(key)
        except Exception as exc:
            failures.append(f"could not restore {key}: {exc!r}")
    return failures


def restore_all() -> list[str]:
    """Puts every value back, newest first; returns one line per value not put back.

    A value not put back stays owned, with the game's own value (2026-09-18). Forgotten, as it was until then, the next
    enable would have read the mod's value still in the game, taken it for the game's own, and never put the real one
    back.
    """
    return restore_each(reversed(list(_entries)))


def unloaded_count() -> int:
    """Values the last restore left to the game, their asset being unloaded."""
    return sum(1 for entry in _entries.values() if entry.get("unloaded"))


def forget_character() -> None:
    for key in [key for key, entry in _entries.items() if entry["scope"] == CHARACTER]:
        del _entries[key]
