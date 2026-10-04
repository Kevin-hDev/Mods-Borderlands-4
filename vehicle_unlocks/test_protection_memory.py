"""Read only private test storage and synthetic bounded FNames."""
import ctypes
import struct
import sys
import unittest
from unittest.mock import patch
from vehicle_unlocks.protection_memory import Memory
from vehicle_unlocks import protection_config as cfg


class Tests(unittest.TestCase):
    def test_real_bounded_read_and_wrong_image_refusal(self):
        memory = Memory()
        buffer = ctypes.create_string_buffer(b'vehicle')
        self.assertEqual(memory.read(ctypes.addressof(buffer), 7), b'vehicle')
        for address, size in ((0, 1), (True, 1), (65536, 0), (65536, cfg.MAX_READ + 1)):
            with self.assertRaises(ValueError):
                memory.read(address, size)
        with self.assertRaises(ValueError):
            memory.identify()

    def test_name_decoder_and_bounds(self):
        memory = Memory()
        base, block, index = 0x140000000, 0x200000, 42
        data = {base + cfg.NAME_POOL_RVA + 16: struct.pack('<Q', block),
                block + index * 2: struct.pack('<H', 5 << 6), block + index * 2 + 2: b'Cello'}
        def read(address, size):
            self.assertEqual(len(data[address]), size)
            return data[address]
        with patch.object(memory, 'identify', return_value=(base, '')), patch.object(memory, 'read', side_effect=read):
            self.assertEqual(memory.name(struct.pack('<II', index, 0)), 'Cello')
            for raw in (b'bad', struct.pack('<II', cfg.MAX_NAME_BLOCKS << 16, 0)):
                with self.assertRaises(ValueError):
                    memory.name(raw)
            data[block + index * 2] = struct.pack('<H', (5 << 6) | 1)
            with self.assertRaises(ValueError):
                memory.name(struct.pack('<II', index, 0))


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    sys.exit(not result.wasSuccessful())
