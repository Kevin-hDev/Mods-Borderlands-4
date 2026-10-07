"""Recognising a camera mode definition from its bytes, and the mode store's table: the values of the game's files are
kept, anything else is not. Table heads and names as trial 8 read them (2026-10-06)."""

import struct
import unittest

from apex_camera_runtime.free_look_definitions import Layout, Mode, entries, named, read_mode, slots, trusted

SHAPE = Layout(blend=0x10, method=0x20, behaviors=0x28)
KEYS = {"ThirdPerson": bytes.fromhex("a4cc010000000000"), "Orbit": bytes.fromhex("01d7010000000000"),
        "Default": bytes.fromhex("0703000000000000")}


def block(blend=0.6, method=0, items=0x2000_0000, count=9, room=9):
    data = bytearray(SHAPE.size)
    struct.pack_into("<f", data, SHAPE.blend, blend)
    struct.pack_into("<i", data, SHAPE.method, method)
    struct.pack_into("<Qii", data, SHAPE.behaviors, items, count, room)
    return bytes(data)


def entry(head_hex: str, address: int) -> bytes:
    return bytes.fromhex(head_hex) + struct.pack("<QQ", address, 0)


TABLE = entries(entry("f6f72dd12e8a5e0000000000dd000000", 0x11D0) + entry("12cba76b070300000000000009000000", 0x1528)
                + entry("1f86d49901d701000000000033000000", 0x16E8) + entry("d9f0e09ca4cc010000000000df000000", 0x1800))


class ReadModeTests(unittest.TestCase):
    def test_third_person_and_orbit_are_recognised_with_their_method(self):
        self.assertEqual(read_mode(block(), SHAPE).text(), "blend=0.6 method=FromCamera behaviors=9")
        self.assertEqual(read_mode(block(method=1), SHAPE).text(), "blend=0.6 method=Fixed behaviors=9")

    def test_a_blend_time_the_game_does_not_use_is_refused(self):
        self.assertIsNone(read_mode(block(blend=0.61), SHAPE))
        self.assertIsNone(read_mode(block(blend=float("nan")), SHAPE))

    def test_an_unknown_method_or_a_broken_list_is_refused(self):
        self.assertIsNone(read_mode(block(method=3), SHAPE))
        self.assertIsNone(read_mode(block(items=0x10), SHAPE))
        self.assertIsNone(read_mode(block(count=0), SHAPE))
        self.assertIsNone(read_mode(block(count=9, room=4), SHAPE))
        self.assertIsNone(read_mode(block(count=40, room=40), SHAPE))

    def test_short_bytes_are_refused(self):
        self.assertIsNone(read_mode(block()[:-1], SHAPE))

    def test_slots_keep_only_values_that_could_be_addresses(self):
        data = struct.pack("<QQQQ", 0x10, 0x2000_0008, 0x2000_0001, 0x8000_0000_0000)
        self.assertEqual(list(slots(data)), [(8, 0x2000_0008)])


class TableTests(unittest.TestCase):
    def test_entries_read_the_head_and_the_address(self):
        self.assertEqual([address for _head, address in TABLE], [0x11D0, 0x1528, 0x16E8, 0x1800])

    def test_the_names_of_trial_8_find_their_modes(self):
        self.assertEqual(named(TABLE, KEYS), {"ThirdPerson": 0x1800, "Orbit": 0x16E8, "Default": 0x1528})

    def test_a_name_found_twice_is_left_out(self):
        twice = TABLE + entries(entry("00000000a4cc01000000000001000000", 0x1900))
        self.assertNotIn("ThirdPerson", named(twice, KEYS))

    def test_the_match_is_trusted_only_with_the_known_values(self):
        good = {"Orbit": Mode(0.6, 1, 9), "ThirdPerson": Mode(0.6, 0, 9), "Default": Mode(0.6, 0, 16)}
        self.assertIsNone(trusted(good))
        self.assertTrue(trusted({**good, "Orbit": Mode(0.6, 0, 9)}).startswith("values_differ"))
        self.assertTrue(trusted({"Orbit": good["Orbit"]}).startswith("names_missing"))


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
