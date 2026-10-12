"""A camera profile's five values keep the sliders' own bounds: a value past them is refused, never clamped; the
camera's current values read as a profile's starting point."""

import sys
import unittest
from types import SimpleNamespace as NS

from profile_test_fixtures import values
from apex_camera_runtime import profile_values as pv
from apex_camera_runtime.camera_distance_options import MAX_CLOSE_M, MAX_FAR_M, MIN_CLOSE_M, MIN_FAR_M
from apex_camera_runtime.constants import FOV_MAX, FOV_MIN
from apex_camera_runtime.framing_catalog import group


def camera(fov_enabled=True, fov=100.0, distances=(140.0, 256.0, 420.0), rows=((15, False), (-40, False), (25, True))):
    return NS(fov_enabled=lambda: fov_enabled, fov_value=lambda: fov, camera_distances=lambda: distances,
              framing_values=lambda: rows)


class ValueTests(unittest.TestCase):
    def test_the_defaults_are_the_sliders_defaults(self):
        self.assertEqual(pv.DEFAULTS, pv.Values(110, 1.8, 3.6, 10, 0))
        self.assertEqual(pv.FIELDS, ("fov", "close", "far", "spacing", "height"))

    def test_each_field_takes_its_sliders_bounds_and_refuses_past_them(self):
        bounds = {"fov": (FOV_MIN, FOV_MAX, 1), "close": (MIN_CLOSE_M, MAX_CLOSE_M, 0.01),
                  "far": (MIN_FAR_M, MAX_FAR_M, 0.01),
                  "spacing": (group("horizontal").minimum, group("horizontal").maximum, 1),
                  "height": (group("height").minimum, group("height").maximum, 1)}
        for field, (low, high, step) in bounds.items():
            with self.subTest(field=field):
                self.assertEqual(pv.checked(field, low), low)
                self.assertEqual(pv.checked(field, high), high)
                for bad in (low - step, high + step, True, None, "1", float("nan"), float("inf")):
                    with self.assertRaises(ValueError):
                        pv.checked(field, bad)

    def test_whole_numbers_stay_whole_and_distances_keep_the_centimetre(self):
        self.assertEqual(pv.checked("fov", 100.0), 100)
        self.assertIs(type(pv.checked("fov", 100.0)), int)
        self.assertIs(type(pv.checked("spacing", -40.0)), int)
        with self.assertRaises(ValueError):
            pv.checked("fov", 100.5)
        with self.assertRaises(ValueError):
            pv.checked("height", 2.5)
        self.assertEqual(pv.checked("close", 1.234), 1.23)
        self.assertEqual(pv.checked("far", 4), 4.0)
        with self.assertRaises(ValueError):
            pv.checked("zoom", 15)

    def test_make_needs_all_five_and_changed_checks_the_new_value(self):
        self.assertEqual(pv.make(fov=100, close=1.4, far=3.2, spacing=-40, height=25),
                         pv.Values(100, 1.4, 3.2, -40, 25))
        with self.assertRaises(ValueError):
            pv.make(fov=100, close=1.4, far=3.2, spacing=-40)
        with self.assertRaises(ValueError):
            pv.make(fov=100, close=1.4, far=3.2, spacing=-40, height=25, zoom=15)
        start = values()
        self.assertEqual(pv.changed(start, "height", 25), values(height=25))
        self.assertEqual(start, pv.DEFAULTS)
        with self.assertRaises(ValueError):
            pv.changed(start, "height", 101)

    def test_the_camera_reads_as_a_profile(self):
        self.assertEqual(pv.from_camera(camera(), 104.6), pv.Values(105, 1.4, 4.2, -40, 25))

    def test_the_fov_on_screen_comes_first_then_the_mods_then_110(self):
        self.assertEqual(pv.from_camera(camera(fov_enabled=True, fov=120.0), None).fov, 120)
        self.assertEqual(pv.from_camera(camera(fov_enabled=False, fov=120.0), None).fov, 110)
        self.assertEqual(pv.from_camera(camera(fov_enabled=False), 90.0).fov, 90)
        self.assertEqual(pv.from_camera(camera(), 40.0).fov, 70)
        self.assertEqual(pv.from_camera(camera(), 170.0).fov, 150)
        self.assertEqual(pv.from_camera(camera(fov_enabled=False), float("nan")).fov, 110)

    def test_a_reading_the_profile_could_not_hold_starts_at_its_default(self):
        odd = camera(distances=("far", 256.0, 900.0), rows=((15, False), (500, False), "bad"))
        self.assertEqual(pv.from_camera(odd, 100.0), pv.Values(100, 1.8, 3.6, 10, 0))
        older = NS(fov_enabled=lambda: False)
        self.assertEqual(pv.from_camera(older, None), pv.DEFAULTS)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ValueTests))
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    sys.exit(not result.wasSuccessful())
