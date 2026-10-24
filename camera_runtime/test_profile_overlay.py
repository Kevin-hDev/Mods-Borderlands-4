"""The elected mod's settings with the shown profile over them: without one every reading passes through; with one the
FOV, the close and far distances, the spacing and the height are the profile's, and nothing else changes."""

import sys
import unittest
from types import SimpleNamespace as NS

from profile_test_fixtures import values
from apex_camera_runtime.camera_distance import CLOSE, FAR, NORMAL
from apex_camera_runtime.profile_overlay import ProfiledSettings


class Shown:
    def __init__(self):
        self.values, self.preview = None, None

    def shown(self):
        return self.values

    def distance(self, chosen):
        return chosen if self.preview is None else self.preview


def mod():
    return NS(fov_enabled=lambda: False, fov_value=lambda: 120.0, camera_distances=lambda: (180.0, 256.0, 360.0),
              camera_distance=lambda: NORMAL, framing_values=lambda: ((15, False), (10, False), (0, False)),
              third_person_enabled=lambda: True, note="kept")


class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.profiles, self.base = Shown(), mod()
        self.settings = ProfiledSettings(self.base, self.profiles)

    def readings(self):
        return tuple(getattr(self.settings, name)() for name in (
            "fov_enabled", "fov_value", "camera_distances", "camera_distance", "framing_values"))

    def test_without_a_profile_every_reading_passes_through(self):
        self.assertEqual(self.readings(), (False, 120.0, (180.0, 256.0, 360.0), NORMAL,
                                           ((15, False), (10, False), (0, False))))
        self.assertIs(self.settings.base, self.base)
        self.assertTrue(self.settings.third_person_enabled())
        self.assertEqual(self.settings.note, "kept")

    def test_each_reading_is_looked_up_once_and_still_follows_the_profile_shown(self):
        looked = []

        class Counted:
            def __getattr__(_self, name):
                looked.append(name)
                return getattr(self.base, name)
        settings = ProfiledSettings(Counted(), self.profiles)
        for _ in range(3):
            settings.third_person_enabled()
            settings.fov_value()
        self.assertEqual(looked, ["third_person_enabled", "fov_value"])
        self.profiles.values = values(fov=100, close=1.4, far=4.2, spacing=-40, height=25)
        self.assertEqual(settings.fov_value(), 100.0)

    def test_a_profile_places_its_five_values_and_keeps_the_zoom_and_the_normal_distance(self):
        self.profiles.values = values(fov=100, close=1.4, far=4.2, spacing=-40, height=25)
        fov_enabled, fov, distances, distance, rows = self.readings()
        self.assertEqual((fov_enabled, fov, distance), (True, 100.0, NORMAL))
        self.assertEqual(distances, (140.0, 256.0, 420.0))
        self.assertEqual(rows, ((15, False), (-40, False), (25, True)))
        self.profiles.values = values(spacing=60, height=100)
        self.assertEqual(self.settings.framing_values(), ((15, False), (60, False), (100, True)))

    def test_the_distance_shown_follows_the_preview(self):
        self.profiles.preview = CLOSE
        self.assertEqual(self.settings.camera_distance(), CLOSE)
        self.profiles.preview = FAR
        self.assertEqual(self.settings.camera_distance(), FAR)

    def test_a_reading_the_mod_does_not_have_stays_missing(self):
        older = ProfiledSettings(NS(fov_enabled=lambda: True, fov_value=lambda: 90.0), self.profiles)
        self.profiles.values = values()
        self.assertIsNone(getattr(older, "camera_distances", None))
        self.assertIsNone(getattr(older, "framing_values", None))
        self.assertEqual(older.fov_value(), 110.0)
        with self.assertRaises(AttributeError):
            older.camera_distance()

    def test_the_base_reading_is_asked_each_time(self):
        self.profiles.values = values()
        calls = []
        self.base.camera_distances = lambda: calls.append(1) or (180.0, 250.0, 360.0)
        self.assertEqual(self.settings.camera_distances(), (180.0, 250.0, 360.0))
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(OverlayTests))
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    sys.exit(not result.wasSuccessful())
