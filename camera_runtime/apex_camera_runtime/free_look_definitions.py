"""Free Look: recognising the game's camera mode definitions in memory, free of the game for its tests.

Each camera mode carries ViewTargetRotationUpdateMethod (CameraModeDef): FromCamera 0, Fixed 1, FromInputDelta 2.
Third person and first person rebuild the view from the camera each frame (FromCamera), which turns the hunter with
the camera; Fixed, the value Orbit uses, lets the camera turn alone (verified in game, 2026-10-06). No field the SDK
reads leads to the definitions: the camera mode store keeps a table of them, entries 0x20 bytes apart, each with the
mode's name at bytes 4 to 8 and the definition's address at +0x10 (store+0x1c8 in build 1.10.2). A block is taken
for a definition only if it holds a camera mode's values, and the table only if its three known modes do.
Investigation: docs/third_person_fov/camera/2026-10-06-lock-view.md, trials 6 to 8.
"""

import math
import struct
from dataclasses import dataclass

TYPE_NAME = "CameraModeDef"
BLEND, METHOD, BEHAVIORS = "blendintime", "viewtargetrotationupdatemethod", "behaviors"
FROM_CAMERA, FIXED = 0, 1
METHODS = {0: "FromCamera", 1: "Fixed", 2: "FromInputDelta"}
# Every BlendInTime of the game's camera_mode file (Nexus-Data-camera_mode0.json, 2026-09-22 extraction).
BLENDS = (0.0, 0.2333, 0.233, 0.25, 0.33, 0.35, 0.433, 0.5, 0.6, 1.0)
LOWEST_ADDRESS = 0x10000
HIGHEST_ADDRESS = 0x7FFF_FFFF_FFFF
MAX_BEHAVIORS = 32
ENTRY = 0x20
VALUE = 0x10
MAX_ENTRIES = 64
MIN_FOUND = 10
NAME_IN_HEAD = slice(4, 8)
NAME_IN_KEY = slice(0, 4)
THIRD_PERSON, ORBIT, FIRST_PERSON = "ThirdPerson", "Orbit", "Default"
NAMES = (THIRD_PERSON, ORBIT, FIRST_PERSON)
FIRST_PERSON_BEHAVIORS = 16


@dataclass(frozen=True)
class Layout:
    blend: int
    method: int
    behaviors: int

    @property
    def size(self) -> int:
        """The behaviours list is the last field: a pointer and two counts."""
        return self.behaviors + 16


@dataclass(frozen=True)
class Mode:
    blend: float
    method: int
    behaviors: int

    def text(self) -> str:
        return f"blend={self.blend:.4g} method={METHODS[self.method]} behaviors={self.behaviors}"


def pointer(value: int) -> bool:
    return LOWEST_ADDRESS <= value <= HIGHEST_ADDRESS and value % 8 == 0


def read_mode(data: bytes, shape: Layout) -> Mode | None:
    """The mode these bytes describe, or None when they are not a camera mode definition."""
    if len(data) < shape.size:
        return None
    blend = struct.unpack_from("<f", data, shape.blend)[0]
    method = struct.unpack_from("<i", data, shape.method)[0]
    items, count, room = struct.unpack_from("<Qii", data, shape.behaviors)
    if not math.isfinite(blend) or not any(abs(blend - known) < 1e-4 for known in BLENDS):
        return None
    if method not in METHODS or not pointer(items) or not 1 <= count <= room <= 2 * MAX_BEHAVIORS:
        return None
    return Mode(blend, method, count) if count <= MAX_BEHAVIORS else None


def slots(data: bytes):
    """(offset, address) of each pointer-sized value that could be an address."""
    for offset in range(0, len(data) - 7, 8):
        value = struct.unpack_from("<Q", data, offset)[0]
        if pointer(value):
            yield offset, value


def entries(data: bytes) -> list:
    """(first 16 bytes, definition address) of each table entry."""
    return [(data[start:start + VALUE], struct.unpack_from("<Q", data, start + VALUE)[0])
            for start in range(0, len(data) - ENTRY + 1, ENTRY)]


def named(table: list, keys: dict) -> dict:
    """Mode name -> definition address, for each name found in exactly one entry's head."""
    result = {}
    for name, key in keys.items():
        matches = [address for head, address in table if head[NAME_IN_HEAD] == key[NAME_IN_KEY]]
        if len(matches) == 1:
            result[name] = matches[0]
    return result


def trusted(modes: dict) -> str | None:
    """Why the match cannot be trusted, or None: Orbit is Fixed, ThirdPerson is not, first person has 16 behaviours."""
    orbit, third, first = modes.get(ORBIT), modes.get(THIRD_PERSON), modes.get(FIRST_PERSON)
    if orbit is None or third is None or first is None:
        return f"names_missing found={sorted(modes)}"
    if orbit.method != FIXED or third.method != FROM_CAMERA or first.behaviors != FIRST_PERSON_BEHAVIORS:
        return f"values_differ orbit={orbit.text()} third={third.text()} first={first.text()}"
    return None
