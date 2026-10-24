"""Container ownership, streaming and exclusion regression tests."""
import struct
import unittest
from types import SimpleNamespace as NS

from apex_camera_runtime.loot_constants import MAX_SCAN
from apex_camera_runtime.loot_fields import LootFields

WORLD = object()


class Memory:
    def __init__(self):
        self.data = {}
        self.fail = False
        self.writes = []

    def read(self, address, size):
        return self.data.get(address)

    def write(self, address, data):
        if self.fail:
            return False
        self.writes.append(address)
        self.data[address] = data
        return True


def actor(path='Chest', address=0x10000, definition='UsabilityData_Lootable_Default'):
    return NS(_path_name=lambda: path, _get_address=lambda: address, gone=False,
              UsabilityConfigInfo=NS(bUseExternalDef=True, bRequireTrace=True,
                                    UsabilityDataDef=NS(_name=definition)))


def weak(obj):
    """The SDK's weak pointer: the object while it lives, None once the game has destroyed it."""
    return lambda: None if obj.gone else obj


class FieldsTests(unittest.TestCase):
    def setUp(self):
        self.objects = [actor(), actor('Vendor', 0x20000, 'UsabilityData_VendingMachine')]
        self.memory = Memory()
        self.original = struct.pack('<Bf', 0, 330)
        for obj in self.objects:
            self.memory.data[obj._get_address() + 0x6D3] = self.original
        self.worlds = []
        self.patch = LootFields(self.listed, self.memory, weak)

    def listed(self, world):
        self.worlds.append(world)
        return iter(self.objects)

    def test_only_loot_and_restore(self):
        self.patch.apply(660, WORLD)
        self.assertEqual(self.memory.data[0x106D3], struct.pack('<Bf', 1, 660))
        self.assertEqual(self.memory.data[0x206D3], self.original)
        self.patch.restore()
        self.assertEqual(self.memory.data[0x106D3], self.original)
        self.assertFalse(self.patch.pending)

    def test_containers_come_from_the_world_given(self):
        self.patch.apply(660, WORLD)
        self.patch.apply(990, WORLD)
        self.assertEqual(self.worlds, [WORLD, WORLD])

    def test_restore_needs_no_search(self):
        self.patch.apply(660, WORLD)
        self.patch.restore()
        self.assertEqual(self.worlds, [WORLD])

    def test_value_change_preserves_original(self):
        self.patch.apply(660, WORLD)
        self.patch.apply(990, WORLD)
        self.patch.restore()
        self.assertEqual(self.memory.data[0x106D3], self.original)

    def test_failed_restore_keeps_ownership(self):
        self.patch.apply(660, WORLD)
        self.memory.fail = True
        with self.assertRaises(RuntimeError):
            self.patch.restore()
        self.assertTrue(self.patch.pending)
        self.memory.fail = False
        self.patch.restore()
        self.assertFalse(self.patch.pending)

    def test_container_out_of_the_world_list_is_still_given_back(self):
        # A cell being unloaded: its container leaves the world's list but the game has not destroyed it yet.
        self.patch.apply(660, WORLD)
        chest = self.objects[0]
        self.objects = [self.objects[1]]
        self.patch.apply(660, WORLD)
        self.assertTrue(self.patch.pending)
        self.patch.restore()
        self.assertEqual(self.memory.data[0x106D3], self.original)
        self.assertFalse(self.patch.pending)
        self.assertFalse(chest.gone)

    def test_destroyed_actor_is_not_written(self):
        self.patch.apply(660, WORLD)
        self.objects[0].gone = True
        self.objects = []
        self.memory.writes.clear()
        self.patch.restore()
        self.assertEqual(self.memory.writes, [])
        self.assertFalse(self.patch.pending)

    def test_container_replaced_at_the_same_place_is_extended(self):
        """Destroyed, then replaced by a new one at the same path and address between two refreshes: the new one,
        holding the game's value, is extended and given back like any other (Kevin, 2026-10-24: « le vieux defaut on
        peut le corriger aussi »)."""
        self.patch.apply(660, WORLD)
        self.objects[0].gone = True
        replacement = actor()
        self.objects = [replacement, self.objects[1]]
        self.memory.data[0x106D3] = self.original
        self.patch.apply(660, WORLD)
        self.assertEqual(self.memory.data[0x106D3], struct.pack('<Bf', 1, 660))
        self.assertIs(self.patch.saved[('Chest', 0x106D3)].pointer(), replacement)
        self.patch.restore()
        self.assertEqual(self.memory.data[0x106D3], self.original)
        self.assertFalse(self.patch.pending)

    def test_destroyed_actor_out_of_the_list_is_forgotten(self):
        self.patch.apply(660, WORLD)
        self.objects[0].gone = True
        self.objects = [self.objects[1]]
        self.patch.apply(660, WORLD)
        self.assertEqual(self.patch.saved, {})
        self.assertFalse(self.patch.pending)

    def test_world_list_is_bounded(self):
        self.objects = [actor(f'Chest{n}', 0x100000 + n * 0x1000) for n in range(MAX_SCAN + 1)]
        # The first chests could be written: the budget is checked before any write, not once they are written
        # (review of 2026-10-24: with no writable chest, a check made late passed too).
        for obj in self.objects[:3]:
            self.memory.data[obj._get_address() + 0x6D3] = self.original
        with self.assertRaisesRegex(RuntimeError, 'scan budget'):
            self.patch.apply(660, WORLD)
        self.assertEqual(self.memory.writes, [])

    def test_world_list_of_exactly_the_budget_is_taken(self):
        self.objects = [actor(f'Chest{n}', 0x100000 + n * 0x1000) for n in range(MAX_SCAN)]
        self.patch.apply(660, WORLD)
        self.assertEqual(self.memory.writes, [])

    def test_other_mod_value_is_not_overwritten(self):
        self.patch.apply(660, WORLD)
        changed = struct.pack('<Bf', 1, 700)
        self.memory.data[0x106D3] = changed
        self.patch.apply(990, WORLD)
        self.patch.restore()
        self.assertEqual(self.memory.data[0x106D3], changed)

    def test_longer_native_distance_is_preserved(self):
        native = struct.pack('<Bf', 1, 900)
        self.memory.data[0x106D3] = native
        self.patch.apply(660, WORLD)
        self.patch.restore()
        self.assertEqual(self.memory.data[0x106D3], native)

    def test_temporarily_unreadable_configuration_keeps_restore_pending(self):
        self.patch.apply(660, WORLD)
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
