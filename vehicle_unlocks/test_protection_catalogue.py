"""Loading references may change; reward links and entitlement addresses may not."""
import struct
import sys
import unittest
from types import SimpleNamespace as NS
from vehicle_unlocks import protection_config as cfg


class Tests(unittest.TestCase):
    def setUp(self):
        try:
            from vehicle_unlocks.protection_catalogue import Catalogue
        except ImportError:
            self.fail('Production catalogue missing')
        self.Catalogue = Catalogue
        self.base, self.cache, self.data, self.kind = 0x140000000, 0x200000, 0x300000, 0x600000
        self.addresses = tuple(0x400000 + i * 0x1000 for i in range(5))
        self.raw = {self.base + r: b for r, b in cfg.BLOCKS}
        self.raw[self.base + cfg.CACHE_RVA] = struct.pack('<Q', self.cache)
        self.raw[self.cache + cfg.ARRAY_OFFSET] = struct.pack('<Qii', self.data, 5, 5)
        self.raw[self.data] = struct.pack('<5Q', *self.addresses)
        self.names = {0: 'None'}
        for i, (key, reward) in enumerate((*((k, v.reward) for k, v in cfg.DLC.items()), ('Banjo', 'RewardPackage_Banjo'))):
            self.names[i * 2 + 1], self.names[i * 2 + 2] = key, reward
            raw = bytearray(cfg.DEFINITION_SIZE)
            raw[56:64] = struct.pack('<Q', i * 2 + 1)
            raw[104:128] = struct.pack('<QQQ', i * 2 + 2, self.kind, 0x700000 + i * 8)
            self.raw[self.addresses[i]] = bytes(raw)
        self.memory = NS(identify=lambda: (self.base, ''), read=self.read,
                         name=lambda b: self.names[struct.unpack('<Q', b)[0]])

    def read(self, address, size):
        result = self.raw[address]
        self.assertEqual(len(result), size)
        return result

    def change(self, index, offset, value):
        raw = bytearray(self.raw[self.addresses[index]])
        raw[offset:offset + len(value)] = value
        self.raw[self.addresses[index]] = bytes(raw)

    def test_loading_field_excluded_but_fact_and_other_rewards_retained(self):
        c = self.Catalogue(self.memory, self.kind)
        before = c.capture()
        self.change(0, 64, b'changed!')
        self.assertEqual(c.capture(), before)
        self.change(0, 144, b'changed!')
        self.assertNotEqual(c.capture()[0], before[0])
        self.setUp()
        c = self.Catalogue(self.memory, self.kind)
        before = c.capture()
        self.change(4, 104, bytes(24))
        self.assertNotEqual(c.capture()[0], before[0])

    def test_target_link_is_separate_from_identity_and_cannot_change_type(self):
        c = self.Catalogue(self.memory, self.kind)
        before = c.capture()
        self.change(0, 104, struct.pack('<QQQ', 0, self.kind, 0))
        after = c.capture()
        self.assertEqual(after[0], before[0])
        self.assertNotEqual(after[1], before[1])
        self.change(0, 112, bytes(8))
        with self.assertRaises(ValueError):
            c.capture()

    def test_version_bounds_duplicate_and_missing_refused(self):
        self.raw[self.base + cfg.BLOCKS[0][0]] = bytes(len(cfg.BLOCKS[0][1]))
        with self.assertRaises(ValueError):
            self.Catalogue(self.memory, self.kind)
        self.setUp()
        self.raw[self.cache + cfg.ARRAY_OFFSET] = struct.pack('<Qii', self.data, 33, 33)
        with self.assertRaises(ValueError):
            self.Catalogue(self.memory, self.kind).capture()
        self.setUp()
        self.raw[self.data] = struct.pack('<5Q', *([self.addresses[0]] * 5))
        with self.assertRaises(ValueError):
            self.Catalogue(self.memory, self.kind).capture()

    def test_only_stable_zero_header_is_pending(self):
        from vehicle_unlocks.protection_catalogue import CataloguePending
        slot = self.cache + cfg.ARRAY_OFFSET
        self.raw[slot] = bytes(16)
        with self.assertRaises(CataloguePending):
            self.Catalogue(self.memory, self.kind).capture()
        for data, count, capacity in ((self.data, 0, 0), (0, -1, 0), (0, 0, 33)):
            self.raw[slot] = struct.pack('<Qii', data, count, capacity)
            with self.assertRaises(ValueError):
                self.Catalogue(self.memory, self.kind).capture()

    def test_named_unloaded_reward_is_valid_but_invalid_pointer_is_not(self):
        c = self.Catalogue(self.memory, self.kind)
        self.change(0, 120, bytes(8))
        c.validate_originals(c.capture()[1])
        self.change(0, 120, struct.pack('<Q', 1))
        with self.assertRaises(ValueError):
            c.validate_originals(c.capture()[1])
        self.change(0, 120, struct.pack('<Q', 2**47))
        with self.assertRaises(ValueError):
            c.validate_originals(c.capture()[1])
        self.change(0, 120, bytes(8))
        self.change(0, 104, bytes(8))
        with self.assertRaises(ValueError):
            c.validate_originals(c.capture()[1])

    def test_non_target_lazy_caches_do_not_invalidate_owned_links(self):
        from vehicle_unlocks.protection_links import Links
        c = self.Catalogue(self.memory, self.kind)
        self.change(4, 112, bytes(16))
        before = c.capture()
        def write(address, expected, value):
            index = self.addresses.index(address - cfg.LINK_OFFSET)
            self.assertEqual(self.raw[self.addresses[index]][104:128], expected)
            self.change(index, 104, value)
        links = Links(c.capture, write)
        links.set(tuple(cfg.DLC))
        # Native code populates these non-owned caches after cold startup.
        self.change(4, 112, struct.pack('<QQ', self.kind, 0x700020))
        self.assertEqual(c.capture()[0], before[0])
        links.check()
        links.set(tuple(cfg.DLC))
        links.set(())
        self.assertEqual(c.capture()[1], before[1])
        self.assertEqual(self.raw[self.addresses[4]][112:128], struct.pack('<QQ', self.kind, 0x700020))
        # A different reward name remains a semantic change, not a loading cache.
        self.change(4, 104, bytes(8))
        with self.assertRaises(RuntimeError):
            links.check()


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    sys.exit(not result.wasSuccessful())
