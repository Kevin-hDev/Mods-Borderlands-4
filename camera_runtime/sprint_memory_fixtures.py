"""A fake game memory holding the player movement definition, for the sprint limit's tests (moved from Omni Sprint's
sdk_stubs.py on 2026-10-09 with the code it tests).

The memory holds a movement component pointing to its definition, laid out as the SDK's type says, with the game
files' values (2026-09-19, verified in game): tests read and write it through apex_camera_runtime.process_memory once
patch() has swapped the Windows calls for this one.
"""

import struct
import sys
import types
from typing import Any

LIMIT_OFFSET = 580
# Case as the SDK gives the names; the code lowers them. The limit sits at 580 as in the 2026-06-26 build.
FIELD_NAMES = (
    "MaxSprintAngle", "SprintAnalogInputThreshold", "MaxSpeedCooldownMaxSpeed", "MaxLadderSlideDownSpeed",
    "FallDelayGravityScale", "MaxLadderDescendSpeed", "LadderSlideAcceleration", "PushAwayFromPlayersRadiusThreshold",
    "DoubleJumpInputDelay", "LadderBrakingDeceleration", "LadderFriction", "LadderSlideBrakingDeceleration",
    "FallDelayTime", "DashInputDelay", "MaxLadderForwardSpeed", "MaxLadderReverseSpeed", "MaxLadderAscendSpeed",
    "JumpQueueTime", "SprintingJumpMaxSpeedPct", "LadderJumpVelocity", "LadderInterpSpeed",
)
OFFSETS = {name: (LIMIT_OFFSET if index == 0 else 16 + index * 8) for index, name in enumerate(FIELD_NAMES)}
BASE = 0x2000_0000
SIZE = 0x40000


class FakeMemory:
    """A block of the game's memory: reads and writes outside it fail, like the Windows calls on a bad address."""

    def __init__(self) -> None:
        self.data = bytearray(SIZE)
        self.refuse_writes = False
        self.writes = 0

    def _inside(self, address: int, size: int) -> bool:
        return BASE <= address and address + size <= BASE + SIZE

    def read(self, address: int, size: int) -> bytes | None:
        return bytes(self.data[address - BASE : address - BASE + size]) if self._inside(address, size) else None

    def write(self, address: int, data: bytes) -> bool:
        if self.refuse_writes or not self._inside(address, len(data)):
            return False
        self.writes += 1
        self.data[address - BASE : address - BASE + len(data)] = data
        return True

    def put_float(self, address: int, value: float) -> None:
        struct.pack_into("<f", self.data, address - BASE, value)

    def get_float(self, address: int) -> float:
        return struct.unpack_from("<f", self.data, address - BASE)[0]

    def put_pointer(self, address: int, value: int) -> None:
        struct.pack_into("<Q", self.data, address - BASE, value)

    def put_definition(self, address: int, known: dict[str, float]) -> None:
        for name, offset in OFFSETS.items():
            self.put_float(address + offset, known[name.lower()])


def movement_type() -> Any:
    """OakCharacterMovementDef as the SDK lists it, with one field the code does not know."""
    fields = [types.SimpleNamespace(Name=name, Offset_Internal=offset) for name, offset in OFFSETS.items()]
    fields.append(types.SimpleNamespace(Name="bCanClimbLadders", Offset_Internal=900))
    return types.SimpleNamespace(Name="OakCharacterMovementDef", _properties=lambda: iter(fields))


def install_types(state: dict) -> None:
    """A fake unrealsdk whose find_all lists state["types"], counting the calls in state["type_finds"]."""
    state.setdefault("types", [movement_type()])
    state.setdefault("type_finds", 0)

    def find_all(cls: str, exact: bool = True) -> Any:
        state["type_finds"] += 1
        return iter([types.SimpleNamespace(Name="Vector", _properties=lambda: iter([])), *state["types"]])

    module = sys.modules.get("unrealsdk") or types.ModuleType("unrealsdk")
    module.find_all = find_all
    sys.modules["unrealsdk"] = module


def patch(fake: FakeMemory) -> None:
    from apex_camera_runtime import process_memory
    process_memory.read, process_memory.write = fake.read, fake.write
