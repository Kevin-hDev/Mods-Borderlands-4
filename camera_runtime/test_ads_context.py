"""Stale weapon/animation/collector references must refuse an ADS publication."""

import sys
import unittest
from types import SimpleNamespace as NS

try:
    from apex_camera_runtime.ads_context import ContextReader
except ModuleNotFoundError:
    ContextReader = None
from apex_camera_runtime.generated_ads import ObjectId
from ads_sdk_test_fixtures import Kind, obj, player


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(ContextReader, "ADS context reader missing")
        self.pc, self.actor, self.manager, self.animation, self.weapon, self.collector = player()
        self.entries = [self.collector]
        self.refs, self.scans = [], 0
        self.live = True

        def weak(item):
            ref = lambda: item if self.live else None
            self.refs.append(ref)
            return ref

        def find(kind):
            self.assertEqual(kind, "OakUIDataCollector_Weapon")
            self.scans += 1
            return iter(self.entries)

        self.reader = ContextReader(weak, self.identify, find)

    @staticmethod
    def identify(item):
        address = item._get_address()
        return ObjectId(address, (address // 16) % 1000, 1)

    def read(self):
        return self.reader.read(self.pc, self.actor, self.manager)

    def test_current_weapon_produces_eight_validated_identities(self):
        sample = self.read()
        self.assertEqual(sample.category, 4)
        self.assertEqual(len(sample.references), 8)
        self.assertEqual(sample.paths.weapon, self.weapon._get_address())
        self.assertEqual(self.scans, 1)
        self.assertIsNotNone(self.read())
        self.assertEqual(self.scans, 1)

    def test_weapon_change_refuses_old_animation_mirror(self):
        self.animation.CurrentWeapon = obj(0x99000)
        self.assertIsNone(self.read())
        self.assertEqual(self.reader.reason, "unknown_weapon")

    def test_missing_animation_is_an_explained_wait(self):
        self.actor.Mesh.GetAnimInstance = lambda: None
        self.assertIsNone(self.read())
        self.assertEqual(self.reader.reason, "animation_pending")

    def test_non_enum_and_out_of_range_category_are_refused(self):
        for value in (5, "sniper", Kind.Invalid):
            self.animation.WeaponType = value
            self.assertIsNone(self.read())

    def test_ambiguous_foreign_and_truncated_collectors_are_refused(self):
        for entries in ([self.collector, self.collector],
                        [NS(Outer=obj(0x88000))], [self.collector] * 1000):
            self.entries = entries
            self.reader.clear()
            self.assertIsNone(self.read())
            self.assertEqual(self.reader.reason, "collector_unavailable")

    def test_weak_reference_expiry_refuses_the_snapshot(self):
        self.assertIsNotNone(self.read())
        self.live = False
        self.assertIsNone(self.read())

    def test_zero_serial_and_foreign_owner_are_refused(self):
        self.reader.identify = lambda item: ObjectId(item._get_address(), 1, 0)
        self.assertIsNone(self.read())
        self.reader.identify = self.identify
        self.pc.OakCharacter = obj(0x88000)
        self.assertIsNone(self.read())


if __name__ == "__main__":
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(ContextTests))
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    sys.exit(not result.wasSuccessful())
