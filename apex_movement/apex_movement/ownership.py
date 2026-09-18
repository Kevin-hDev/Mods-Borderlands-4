"""Owns every game value Apex Movement writes: keeps the game's own value at the first write and puts it back.

Design decision 4: the mod is the only authority on the values it writes, and restores all of them when it stops.
Character values die with the character on a level change, so they are forgotten rather than written back into a
destroyed object; asset values (Move_Slide, jump goals) outlive characters and are always restored.
"""

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


def write(key: str, scope: str, get: Callable[[], Any], put: Callable[[Any], None], value: Any) -> None:
    if key not in _entries:
        _entries[key] = {"scope": scope, "put": put, "original": get()}
    else:
        _entries[key]["put"] = put
    put(value)


def is_owned(key: str) -> bool:
    return key in _entries


def original(key: str) -> Any:
    return _entries[key]["original"]


def restore(key: str) -> None:
    entry = _entries.get(key)
    if entry is None:
        return
    entry["put"](entry["original"])
    # Forgotten only once put back: after a put that fails, such as while the game has unloaded the asset, the game's
    # value is still here for the next try instead of lost for good.
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


def forget_character() -> None:
    for key in [key for key, entry in _entries.items() if entry["scope"] == CHARACTER]:
        del _entries[key]
