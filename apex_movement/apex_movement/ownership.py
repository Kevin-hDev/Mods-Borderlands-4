"""Owns every game value Apex Movement writes: keeps the game's own value at the first write and puts it back.

Design decision 4: the mod is the only authority on the values it writes, and restores all of them when it stops.
Character values die with the character on a level change, so they are forgotten rather than written back into a
destroyed object; asset values (Move_Slide, jump goals) outlive characters and are always restored.
"""

from typing import Any, Callable

CHARACTER = "character"
ASSET = "asset"

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
    entry = _entries.pop(key, None)
    if entry is not None:
        entry["put"](entry["original"])


def restore_all() -> list[str]:
    """Puts every value back, newest first; returns one line per value that could not be put back."""
    failures: list[str] = []
    for key in reversed(list(_entries)):
        try:
            restore(key)
        except Exception as exc:
            _entries.pop(key, None)
            failures.append(f"could not restore {key}: {exc!r}")
    return failures


def forget_character() -> None:
    for key in [key for key, entry in _entries.items() if entry["scope"] == CHARACTER]:
        del _entries[key]
