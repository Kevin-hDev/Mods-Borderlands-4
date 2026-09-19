"""The player movement definition: where its known values sit, how to recognise it, how to find it.

No field the SDK reads leads to it, and a pointer built from its name stays empty (2026-09-19, verified in game). The
movement component keeps its address (+0x1cf0 in the 2026-06-26 build), so each pointer-sized value in the
component's first 16 KB is tried, and kept only if the block it points to holds the game files' values. The offsets
come from the SDK's own type: an update that moves the fields keeps working, one that changes the values finds
nothing and writes nothing.
"""

import struct
from dataclasses import dataclass

import unrealsdk

from . import memory

TYPE_NAME = "OakCharacterMovementDef"
LIMIT = "maxsprintangle"
GAME_LIMIT = 60.0
# CharMove_Player_Defaults in the game's own settings files (character_movement), float fields only; the four
# characters' sheets override none of them.
KNOWN = {
    LIMIT: GAME_LIMIT, "sprintanaloginputthreshold": 0.6, "maxspeedcooldownmaxspeed": 1200.0,
    "maxladderslidedownspeed": 450.0, "falldelaygravityscale": 0.65, "maxladderdescendspeed": 240.0,
    "ladderslideacceleration": 1750.0, "pushawayfromplayersradiusthreshold": 130.0, "doublejumpinputdelay": 0.225,
    "ladderbrakingdeceleration": 2048.0, "ladderfriction": 8.0, "ladderslidebrakingdeceleration": 1200.0,
    "falldelaytime": 0.25, "dashinputdelay": 0.575, "maxladderforwardspeed": 600.0, "maxladderreversespeed": 600.0,
    "maxladderascendspeed": 300.0, "jumpqueuetime": 0.1, "sprintingjumpmaxspeedpct": 0.8, "ladderjumpvelocity": 500.0,
    "ladderinterpspeed": 350.0,
}
COMPONENT_WINDOW = 0x4000
LOWEST_ADDRESS = 0x10000
HIGHEST_ADDRESS = 0x7FFF_FFFF_FFFF
ANGLE_RANGE = (1.0, 180.0)


@dataclass(frozen=True)
class Layout:
    """Offset of each known value in the definition."""

    offsets: dict[str, int]

    @property
    def limit(self) -> int:
        return self.offsets[LIMIT]

    @property
    def size(self) -> int:
        return max(self.offsets.values()) + 4


@dataclass(frozen=True)
class Found:
    address: int
    slot: int


def layout() -> Layout | None:
    """The known values' offsets in the SDK's type, or None when the type or one of the values is missing."""
    for found in unrealsdk.find_all("ScriptStruct", exact=False):
        if str(found.Name) != TYPE_NAME:
            continue
        offsets = {
            str(prop.Name).lower(): int(prop.Offset_Internal)
            for prop in found._properties()
            if str(prop.Name).lower() in KNOWN
        }
        return Layout(offsets) if len(offsets) == len(KNOWN) else None
    return None


def recognised(address: int, shape: Layout) -> bool:
    """Every known value but the limit is the game files' one, and the limit is an angle: 180 when the mod opened it."""
    data = memory.read(address, shape.size)
    if data is None:
        return False
    for name, offset in shape.offsets.items():
        value = struct.unpack_from("<f", data, offset)[0]
        if name == LIMIT:
            if not ANGLE_RANGE[0] <= value <= ANGLE_RANGE[1]:
                return False
        elif abs(value - KNOWN[name]) > 1e-4 * max(1.0, abs(KNOWN[name])):
            return False
    return True


def find(component: int, shape: Layout) -> Found | None:
    """The definition the movement component at this address points to, or None."""
    data = memory.read(component, COMPONENT_WINDOW)
    if data is None:
        return None
    for slot in range(0, COMPONENT_WINDOW, 8):
        address = struct.unpack_from("<Q", data, slot)[0]
        if LOWEST_ADDRESS <= address <= HIGHEST_ADDRESS and recognised(address, shape):
            return Found(address, slot)
    return None
