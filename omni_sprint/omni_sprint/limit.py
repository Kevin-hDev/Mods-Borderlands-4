"""Opens the sprint limit of each movement definition the player uses, and puts back what it found there.

The value found before the mod is kept at its first write, per definition. A definition already at 180 the first time
keeps the game files' 60, since nothing else in the game writes this value. Nothing is written to a definition that is
no longer recognised: memory the game freed or reused is left alone.
"""

from . import definition, memory

OPEN = 180.0
# Bounded: the game holds 7 player movement definitions (2026-09-19 scan); past this, a new one is not opened.
MAX_OPENED = 16


class Lost(Exception):
    """The definition is no longer where it was: the caller looks for it again."""


class NotOpened(Exception):
    """The definition is there but its limit could not be opened: the caller leaves it alone."""


_originals: dict[int, float] = {}


def hold(address: int, shape: definition.Layout) -> str | None:
    """Keeps this definition's limit at 180; the line to log when it had to write."""
    if not definition.recognised(address, shape):
        raise Lost(f"movement definition at {address:#x} no longer recognised")
    where = address + shape.limit
    current = memory.read_float(where)
    if current is None:
        raise Lost(f"movement definition at {address:#x}: limit unreadable")
    first = address not in _originals
    if first:
        if len(_originals) >= MAX_OPENED:
            raise NotOpened(f"movement definition at {address:#x} not opened: {MAX_OPENED} already held")
        _originals[address] = current if current != OPEN else definition.GAME_LIMIT
    if current == OPEN:
        return None
    if not memory.write_float(where, OPEN):
        raise NotOpened(f"movement definition at {address:#x}: write refused, limit stays {current:g}")
    if first:
        return f"sprint opened in every direction, movement definition at {address:#x}, game limit {current:g}"
    return f"limit found back at {current:g} in the movement definition at {address:#x}, opened again"


def put_back(shape: definition.Layout | None) -> tuple[int, int]:
    """(put back, left alone) over every definition opened."""
    restored = left = 0
    for address, original in _originals.items():
        where = address + shape.limit if shape is not None else 0
        if (
            shape is not None
            and definition.recognised(address, shape)
            and memory.read_float(where) == OPEN
            and memory.write_float(where, original)
        ):
            restored += 1
        else:
            left += 1
    _originals.clear()
    return restored, left
