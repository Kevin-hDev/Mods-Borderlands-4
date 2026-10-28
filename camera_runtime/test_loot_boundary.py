"""Validate the real native exports and bounded process-memory access outside the game."""
import ctypes
import struct
import unittest
from pathlib import Path

from apex_camera_runtime.loot_memory import ProcessMemory
from apex_camera_runtime.loot_bridge import LIBRARY_NAME


class BoundaryTests(unittest.TestCase):
    def test_real_library_refuses_invalid_abi_and_unrecognized_process(self):
        library = ctypes.CDLL(str(Path(__file__).parent / 'apex_camera_runtime/assets' / LIBRARY_NAME))
        library.loot_start.argtypes = [ctypes.c_uint32, ctypes.c_float]
        library.loot_distance.argtypes = [ctypes.c_float]
        self.assertEqual(library.loot_start(0, 660), 1)
        self.assertEqual(library.loot_start(1, float('nan')), 1)
        self.assertNotEqual(library.loot_start(1, 660), 0)
        self.assertNotEqual(library.loot_distance(660), 0)
        self.assertEqual(library.loot_stop(), 0)

    def test_memory_reads_and_writes_only_five_bytes(self):
        buffer = ctypes.create_string_buffer(b'XXXXXXXXXX')
        address = ctypes.addressof(buffer)
        memory = ProcessMemory()
        value = struct.pack('<Bf', 1, 660)
        self.assertTrue(memory.write(address, value))
        self.assertEqual(memory.read(address, 5), value)
        self.assertEqual(buffer.raw[5:10], b'XXXXX')
        self.assertFalse(memory.write(address, b'bad'))
        self.assertIsNone(memory.read(address, 6))
        self.assertIsNone(memory.read(0, 5))


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
