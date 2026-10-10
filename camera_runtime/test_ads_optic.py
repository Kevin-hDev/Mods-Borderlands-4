"""The optics: one factor per zoom, x1 a light zoom the same on every weapon, the zoom key goes up the ticked zooms and back, the next aim
with a weapon type starts on its last zoom used, "BDL4" (nothing ticked) leaves the game's own aim, and a mod or a
.dll from before every weapon's row keeps the aim each weapon had."""

import math
import unittest
from types import SimpleNamespace as NS

from apex_camera_runtime.ads_optic import CHOICES, ZOOMS, OpticLink, Optics, held_zoom, read_ticked, scale


class Native:
    def __init__(self, optics=True, heavy=True):
        self.optics, self.heavy, self.calls = optics, heavy, []

    def set_optic(self, generation, value):
        self.calls.append((generation, value))


class OpticTests(unittest.TestCase):
    def test_each_zoom_is_that_many_times_narrower_than_the_view_without_aiming(self):
        self.assertEqual(ZOOMS, (2, 3, 4, 6, 8))
        for zoom in ZOOMS:
            view = 2 * math.degrees(math.atan(math.tan(math.radians(55)) * scale(zoom)))
            self.assertAlmostEqual(math.tan(math.radians(view / 2)), math.tan(math.radians(55)) / zoom)
        self.assertAlmostEqual(2 * math.degrees(math.atan(math.tan(math.radians(55)) * scale(2))), 71.0593, 3)

    def test_x1_is_a_light_zoom_the_same_on_every_weapon(self):
        self.assertEqual(scale(1), 0.75)

    def test_kevins_zooms_per_weapon_type(self):
        self.assertEqual(CHOICES, {1: (1, 2, 3), 2: (1, 2, 3, 4), 3: (1, 2), 4: (1, 2, 3, 4), 5: (2, 3, 4, 6, 8),
                                   6: (1, 2)})

    def test_bdl4_has_no_zoom(self):
        optics = Optics()
        self.assertIsNone(optics.current(()))
        self.assertIsNone(optics.next(()))

    def test_one_ticked_zoom_stays(self):
        optics = Optics()
        self.assertEqual(optics.current((6,)), 6)
        self.assertEqual(optics.next((6,)), 6)

    def test_the_key_goes_up_and_back_to_the_smallest(self):
        optics = Optics()
        ticked = (2, 4, 6)
        self.assertEqual(optics.current(ticked), 2)
        self.assertEqual([optics.next(ticked) for _ in range(4)], [4, 6, 2, 4])

    def test_the_next_aim_starts_on_the_last_zoom_used(self):
        optics = Optics()
        optics.next((3, 6))
        self.assertEqual(optics.current((3, 6)), 6)

    def test_a_zoom_no_longer_ticked_starts_from_the_smallest(self):
        optics = Optics()
        optics.next((3, 6))
        self.assertEqual(optics.current((2, 8)), 2)
        self.assertEqual(optics.next((2, 8)), 8)



class LinkTests(unittest.TestCase):
    def settings(self, **rows):
        return NS(weapon_optics=lambda category: rows.get(str(category), ()), sniper_optics=lambda: rows.get("5", ()))

    def test_a_mod_from_before_the_rows_keeps_the_aim_each_weapon_had(self):
        old = NS(sniper_optics=lambda: (3,))
        self.assertEqual([read_ticked(old, category) for category in range(1, 7)],
                         [(1,), (1,), (1,), (1,), (3,), ()])
        self.assertEqual(read_ticked(NS(), 5), ())

    def test_a_value_out_of_the_row_is_bdl4(self):
        for value in ((6,), (2, 1), (1, 1), [1], None, (True,)):
            with self.subTest(value=value):
                self.assertEqual(read_ticked(NS(weapon_optics=lambda _category: value), 1), ())
        self.assertEqual(read_ticked(self.settings(), 7), ())

    def test_a_dll_without_optics_keeps_x1_only(self):
        link = OpticLink()
        settings = self.settings(**{"1": (1, 3), "4": (2, 3), "5": (2,)})
        self.assertTrue(link.allows(settings, Native(optics=False), 1))
        self.assertEqual(link.ticked, (1,))
        self.assertFalse(link.allows(settings, Native(optics=False), 4))
        self.assertFalse(link.allows(settings, Native(optics=False), 5))
        self.assertTrue(link.allows(settings, Native(), 4))

    def test_a_dll_that_refuses_heavy_weapons_keeps_them_on_bdl4(self):
        link = OpticLink()
        settings = self.settings(**{"6": (1, 2), "3": (1, 2)})
        self.assertFalse(link.allows(settings, Native(heavy=False), 6))
        self.assertTrue(link.allows(settings, Native(heavy=False), 3))
        self.assertTrue(link.allows(settings, Native(), 6))

    def test_x1_is_set_at_once_and_keeps_the_weapons_sensitivity_row(self):
        link, native = OpticLink(), Native()
        link.allows(self.settings(**{"1": (1, 2)}), native, 1)
        link.publish(native, 7)
        self.assertEqual(native.calls, [(7, 0.75)])
        self.assertIsNone(held_zoom(NS(ads=NS(optic=link))))
        link.release(native)
        self.assertEqual(native.calls, [(7, 0.75), (7, 1.0)])
        self.assertFalse(link.active)

    def test_without_the_dlls_optics_x1_keeps_the_weapons_own_zoom_and_curve(self):
        link, native = OpticLink(), Native(optics=False)
        link.allows(self.settings(**{"1": (1, 2)}), native, 1)
        link.publish(native, 7)
        link.release(native)
        self.assertEqual(native.calls, [])

    def test_a_magnifying_zoom_goes_at_once_on_release(self):
        link, native = OpticLink(), Native()
        link.allows(self.settings(**{"6": (2,)}), native, 6)
        link.publish(native, 3)
        self.assertEqual(held_zoom(NS(ads=NS(optic=link))), 2)
        link.release(native)
        self.assertEqual(native.calls, [(3, 0.5), (3, 1.0)])
        self.assertIsNone(held_zoom(NS(ads=NS(optic=link))))

    def test_each_weapon_type_remembers_its_own_last_zoom(self):
        link, native = OpticLink(), Native()
        settings = self.settings(**{"2": (1, 2, 4), "5": (3, 8)})
        link.allows(settings, native, 2)
        link.publish(native, 1)
        self.assertEqual(link.next(native), 2)
        link.clear()
        link.allows(settings, native, 5)
        link.publish(native, 2)
        self.assertEqual(link.next(native), 8)
        link.clear()
        link.allows(settings, native, 2)
        link.publish(native, 3)
        self.assertEqual(link.zoom, 2)
        self.assertEqual(native.calls[-1], (3, 0.5))


if __name__ == "__main__":
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case)
                               for case in (OpticTests, LinkTests))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
