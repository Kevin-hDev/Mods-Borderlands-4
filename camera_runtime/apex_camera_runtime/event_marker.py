"""The C++ type marker in front of an animation event the SDK wrote.

The SDK writes a structure into zeroed memory field by field, without building it the way the game does (the grenade
crash, docs/investigations/third_person_fov/camera/2026-09-27-projectiles-deportes.md). An animation event added that
way had 0x0 in its first 8 bytes, where the game's own events hold an address, and its first field starts at byte 8
(trial 10 of the reload sound, 2026-10-25): those bytes are the marker of the event's C++ type, which the engine
reads to work out the event's instant (non vérifié: the engine's source as remembered). Left at zero, the engine would
read it at the next reload. The game's marker is copied over, through process_memory.py: a wrong address fails
instead of crashing the game.
"""

from typing import Any, Callable

MARKER_BYTES = 8
# Below this, a word is no address in the game, so no type marker.
LOWEST_ADDRESS = 0x10000


def first_field(event: Any) -> int:
    """Where the structure's first field starts: the bytes before it are no field."""
    return min(int(field.Offset_Internal) for kind in event._type._superfields() for field in kind._properties())


def marker_of(model: Any, read: Callable[[int, int], bytes | None]) -> bytes | None:
    """The marker of an event the game built, b"" when its fields leave no room for one, None when it cannot be read."""
    if first_field(model) < MARKER_BYTES:
        return b""
    found = read(int(model._get_address()), MARKER_BYTES)
    if found is None or len(found) != MARKER_BYTES or int.from_bytes(found, "little") < LOWEST_ADDRESS:
        return None
    return found


def ensure(event: Any, marker: bytes, read: Callable[[int, int], bytes | None],
           write: Callable[[int, bytes], bool]) -> bool:
    """True once the event holds the game's marker (or there is none to hold); False when it could not be written."""
    if not marker:
        return True
    where = int(event._get_address())
    if read(where, MARKER_BYTES) == marker:
        return True
    return write(where, marker) and read(where, MARKER_BYTES) == marker
