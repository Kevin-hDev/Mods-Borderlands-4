"""The memory calls for real, on this process: a read, a write, and a bad address failing instead of crashing."""

import ctypes
import struct
import unittest

from apex_camera_runtime import process_memory as memory


class ProcessMemoryTests(unittest.TestCase):
    def setUp(self):
        self.block = ctypes.create_string_buffer(struct.pack("<fi", 60.0, 7))
        self.address = ctypes.addressof(self.block)

    def test_bytes_floats_and_ints_are_read(self):
        self.assertEqual(memory.read(self.address, 8), struct.pack("<fi", 60.0, 7))
        self.assertEqual(memory.read_float(self.address), 60.0)
        self.assertEqual(memory.read_int(self.address + 4), 7)

    def test_a_write_changes_only_its_own_value(self):
        self.assertTrue(memory.write_int(self.address + 4, 1))
        self.assertEqual(struct.unpack("<fi", self.block.raw[:8]), (60.0, 1))
        self.assertTrue(memory.write_float(self.address, 180.0))
        self.assertEqual(struct.unpack("<fi", self.block.raw[:8]), (180.0, 1))

    def test_a_bad_address_fails_instead_of_crashing(self):
        self.assertIsNone(memory.read(0x10, 4))
        self.assertIsNone(memory.read_int(0x10))
        self.assertFalse(memory.write_int(0x10, 1))
        self.assertFalse(memory.write_float(0x10, 1.0))


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
