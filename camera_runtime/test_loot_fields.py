"""Container ownership, streaming and exclusion regression tests."""
import struct
import unittest
from types import SimpleNamespace as NS

from apex_camera_runtime.loot_fields import LootFields


class Memory:
    def __init__(self):
        self.data = {}
        self.fail = False

    def read(self, address, size):
        return self.data.get(address)

    def write(self, address, data):
        if self.fail:
            return False
        self.data[address] = data
        return True


def actor(path='Chest', address=0x10000, definition='UsabilityData_Lootable_Default'):
    return NS(_path_name=lambda: path, _get_address=lambda: address,
              UsabilityConfigInfo=NS(bUseExternalDef=True, bRequireTrace=True,
                                    UsabilityDataDef=NS(_name=definition)))


class FieldsTests(unittest.TestCase):
    def setUp(self):
        self.objects = [actor(), actor('Vendor', 0x20000, 'UsabilityData_VendingMachine')]
        self.memory = Memory()
        self.original = struct.pack('<Bf', 0, 330)
        for obj in self.objects:
            self.memory.data[obj._get_address() + 0x6D3] = self.original
        self.patch = LootFields(lambda: iter(self.objects), self.memory)

    def test_only_loot_and_restore(self):
        self.patch.apply(660)
        self.assertEqual(self.memory.data[0x106D3], struct.pack('<Bf', 1, 660))
        self.assertEqual(self.memory.data[0x206D3], self.original)
        self.patch.restore()
        self.assertEqual(self.memory.data[0x106D3], self.original)
        self.assertFalse(self.patch.pending)

    def test_value_change_preserves_original(self):
        self.patch.apply(660)
        self.patch.apply(990)
        self.patch.restore()
        self.assertEqual(self.memory.data[0x106D3], self.original)

    def test_failed_restore_keeps_ownership(self):
        self.patch.apply(660)
        self.memory.fail = True
        with self.assertRaises(RuntimeError):
            self.patch.restore()
        self.assertTrue(self.patch.pending)
        self.memory.fail = False
        self.patch.restore()
        self.assertFalse(self.patch.pending)

    def test_destroyed_actor_is_not_written(self):
        self.patch.apply(660)
        self.objects = []
        self.patch.restore()
        self.assertFalse(self.patch.pending)

    def test_other_mod_value_is_not_overwritten(self):
        self.patch.apply(660)
        changed = struct.pack('<Bf', 1, 700)
        self.memory.data[0x106D3] = changed
        self.patch.apply(990)
        self.patch.restore()
        self.assertEqual(self.memory.data[0x106D3], changed)

    def test_longer_native_distance_is_preserved(self):
        native = struct.pack('<Bf', 1, 900)
        self.memory.data[0x106D3] = native
        self.patch.apply(660)
        self.patch.restore()
        self.assertEqual(self.memory.data[0x106D3], native)

    def test_temporarily_unreadable_configuration_keeps_restore_pending(self):
        self.patch.apply(660)
        config = self.objects[0].UsabilityConfigInfo
        self.objects[0].UsabilityConfigInfo = None
        with self.assertRaises(RuntimeError): self.patch.restore()
        self.assertTrue(self.patch.pending)
        self.objects[0].UsabilityConfigInfo = config
        self.patch.restore()
        self.assertFalse(self.patch.pending)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
