"""Reading, writing and giving back a GbxParam where the game keeps it: a camp's numbers of enemies, the chance and the
rests of an enemy's dodges (decisions 81 and 85). The one place It Follows writes raw memory.

Why: the SDK hands a GbxParam out as 56 bytes with no field (enemy research, séances 6 and 21). Trial 21 read them in
game (docs/RUN/enquetes/2026-10-15-essai-21-esquives-et-valeurs-cachees.md, vérifié en jeu: 12 camps' numbers against
the game's own GetNumTotalActors, 8 dodge families): the 8 bytes at +0 are 0 when the value is in place; the byte at
+40 says its kind, 2 a whole number at +8, 3 a decimal one at +8, 11 a range of two floats at +8 and +12, its centre
and half width; the mark at +32 says how many bytes the value takes. Trials 22 to 27 wrote there and gave back without
a crash, through the probes run_param_bytes.py and run_param_write.py, of which this is the mod's copy (decision 45).

Nothing is read or written unless the SDK says the field is a GbxParam of 56 bytes, lying where its owner's layout puts
it, at the same place on two asks: a copy made for Python moves from one ask to the next, and a write there would land
nowhere, or in memory the game has given to something else. An address is never kept from one call to the next: each
is found again through the SDK from a live owner. Only a value in place, of a known kind, at the size that kind takes,
is written, then read back.
"""

import ctypes
import math
import struct
from typing import Any, Callable

SIZE = 56
TYPE = "GbxParam"
WHOLE, DECIMAL, RANGE = 2, 3, 11
VALUE_AT = 8
# kind -> how its value is packed at VALUE_AT, and the size the mark at +32 gives it.
PACKING = {WHOLE: ("<i", 4), DECIMAL: ("<f", 4), RANGE: ("<ff", 8)}


def _number(value: float) -> float | None:
    return round(value, 4) if math.isfinite(value) else None


def decode(raw: bytes) -> tuple[int, Any]:
    """The kind read at +40, and the value: None when not in place, empty, not a number, or of a kind not written."""
    pointer, = struct.unpack_from("<Q", raw, 0)
    mark, = struct.unpack_from("<H", raw, 32)
    kind = raw[40]
    if pointer != 0 or kind not in PACKING or mark != PACKING[kind][1]:
        return kind, None
    if kind == WHOLE:
        return kind, struct.unpack_from("<i", raw, VALUE_AT)[0]
    first, spread = (_number(value) for value in struct.unpack_from("<ff", raw, VALUE_AT))
    if kind == DECIMAL:
        return kind, first
    return kind, None if first is None or spread is None else [first, spread]


def where(owner: Any, name: str) -> int | str:
    """Where the field lies, or why it is not touched; raises when the SDK cannot answer."""
    layout = owner._type if hasattr(owner, "_type") else owner.Class
    prop = layout._find_prop(name)
    if int(prop.ElementSize) != SIZE:
        return "size"
    first, second = getattr(owner, name), getattr(owner, name)
    if str(first._type.Name) != TYPE:
        return "type"
    address, again = int(first._get_address()), int(second._get_address())
    if address == 0 or address != again:
        return "moving"
    if address != int(owner._get_address()) + int(prop.Offset_Internal):
        return "outside_owner"
    return address


def _found(owner: Any, name: str) -> int | str:
    try:
        return where(owner, name)
    except Exception as error:
        return f"unreadable:{type(error).__name__}"


def read(owner: Any, name: str) -> tuple[int, Any] | str:
    """(kind, value), or why the field was not read."""
    found = _found(owner, name)
    return found if isinstance(found, str) else decode(ctypes.string_at(found, SIZE))


def _pack(kind: int, value: Any) -> bytes:
    form = PACKING[kind][0]
    return struct.pack(form, *value) if kind == RANGE else struct.pack(form, value)


def change(owner: Any, name: str, rule: Callable[[int, Any], Any]) -> dict:
    """Writes rule(kind, value) in place of the value: the value before and after, and the bytes before and after for
    the give back ("old", "new"); or {"refused": why}."""
    found = _found(owner, name)
    if isinstance(found, str):
        return {"refused": found}
    kind, value = decode(ctypes.string_at(found, SIZE))
    if value is None:
        return {"refused": f"kind:{kind}"}
    size = PACKING[kind][1]
    old = ctypes.string_at(found + VALUE_AT, size)
    new = _pack(kind, rule(kind, value))
    ctypes.memmove(found + VALUE_AT, new, size)
    after = ctypes.string_at(found + VALUE_AT, size)
    if after != new:
        return {"refused": "not_read_back", "old": old.hex()}
    return {"kind": kind, "before": value, "after": decode(ctypes.string_at(found, SIZE))[1], "old": old.hex(),
            "new": new.hex()}


def replace(owner: Any, name: str, expected: str, wanted: str) -> str:
    """Writes the bytes wanted where the bytes expected still lie: "written"; "already" when wanted lies there;
    "different" when the game has put others, which are left; or "refused:" and why. Both are hex, as change gives
    them, so that a give back is replace(owner, name, new, old)."""
    found = _found(owner, name)
    if isinstance(found, str):
        return f"refused:{found}"
    target, have = bytes.fromhex(wanted), bytes.fromhex(expected)
    kind, value = decode(ctypes.string_at(found, SIZE))
    if value is None or len(target) != PACKING[kind][1] or len(have) != len(target):
        return f"refused:kind:{kind}"
    at = found + VALUE_AT
    now = ctypes.string_at(at, len(target))
    if now == target:
        return "already"
    if now != have:
        return "different"
    ctypes.memmove(at, target, len(target))
    return "written"
