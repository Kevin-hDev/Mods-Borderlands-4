"""Finding the three camera mode definitions in a fake memory laid out as trial 8 read the game's (2026-10-06)."""

import struct
import unittest
from types import SimpleNamespace as NS

from apex_camera_runtime.free_look_lookup import find

OFFSETS = {"BlendInTime": 0x18, "ViewTargetRotationUpdateMethod": 0x20, "Behaviors": 0x28}
STORE, TABLE, KEY_HOLDER = 0x1000_0000, 0x2000_0000, 0x3000_0000
NAMES = {"ThirdPerson": 0x1CCA4, "Orbit": 0x1D701, "Default": 0x307}


class Memory:
    def __init__(self):
        self.blocks = {}

    def put(self, address, data):
        self.blocks[address] = bytearray(data)

    def read(self, address, size):
        for start, data in self.blocks.items():
            if start <= address and address + size <= start + len(data):
                return bytes(data[address - start:address - start + size])
        return None


def definition(method, behaviors):
    data = bytearray(0x38)
    struct.pack_into("<f", data, 0x18, 0.6)
    struct.pack_into("<i", data, 0x20, method)
    struct.pack_into("<Qii", data, 0x28, 0x5000_0000, behaviors, behaviors)
    return bytes(data)


def game(memory, orbit_method=1, extra=12):
    """A store pointing to a table of 3 named modes and `extra` other modes."""
    memory.put(STORE, struct.pack("<Q", 0) * 0x39 + struct.pack("<Q", TABLE) + bytes(0x400))
    rows = bytearray()
    named = [("ThirdPerson", 0, 9), ("Orbit", orbit_method, 9), ("Default", 0, 16)]
    for index, (name, method, behaviors) in enumerate(named + [(None, 0, 9)] * extra):
        address = 0x4000_0000 + index * 0x100
        memory.put(address, definition(method, behaviors))
        name_bytes = struct.pack("<I", NAMES[name]) if name else struct.pack("<I", 0x9000 + index)
        rows += struct.pack("<I", 0xABCD) + name_bytes + bytes(8) + struct.pack("<QQ", address, 0)
    memory.put(TABLE, rows + bytes(0x800))
    for index, (name, value) in enumerate(NAMES.items()):
        memory.put(KEY_HOLDER + index * 0x10, struct.pack("<Q", value))


def sdk():
    def prop(name, offset):
        return NS(Name=name, Offset_Internal=offset)

    types = [NS(Name="CameraModeDef", _properties=lambda: [prop(n, o) for n, o in OFFSETS.items()]),
             NS(Name="DefaultCameraModeConfig", _properties=lambda: [prop("CameraModeName", 0)])]
    stores = [NS(Name="Default__NexusConfigStoreCameraMode", _get_address=lambda: 0x10),
              NS(Name="NexusConfigStoreCameraMode_0", _get_address=lambda: STORE)]

    def find_all(type_name, exact=True):
        return iter(types if type_name == "ScriptStruct" else stores)

    def make_struct(_type_name, CameraModeName):
        index = list(NAMES).index(CameraModeName)
        return NS(_get_address=lambda: KEY_HOLDER + index * 0x10)

    return NS(find_all=find_all, make_struct=make_struct)


class LookupTests(unittest.TestCase):
    def test_the_three_modes_are_found_by_name(self):
        memory = Memory()
        game(memory)
        found = find(sdk(), memory)
        self.assertEqual(found.shape.method, 0x20)
        self.assertEqual(found.addresses, {"ThirdPerson": 0x4000_0000, "Orbit": 0x4000_0100, "Default": 0x4000_0200})

    def test_a_table_whose_known_values_differ_is_refused(self):
        memory = Memory()
        game(memory, orbit_method=0)
        with self.assertRaisesRegex(LookupError, "not trusted"):
            find(sdk(), memory)

    def test_too_few_modes_is_not_the_table(self):
        memory = Memory()
        game(memory, extra=2)
        with self.assertRaisesRegex(LookupError, "not found"):
            find(sdk(), memory)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
