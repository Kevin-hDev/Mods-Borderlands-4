"""Unknown or excluded weapons must never enter shoulder ADS."""

import sys
import unittest

try:
    from apex_camera_runtime.ads_policy import decide
except ModuleNotFoundError:
    decide = None


class PolicyTests(unittest.TestCase):
    def choose(self, category=4, **changes):
        self.assertIsNotNone(decide, "ADS policy missing")
        arguments = dict(aiming=True, enabled=True, foot_mode="ThirdPerson",
                         vehicle=False, pending=False, supported=True, category=category)
        return decide(**(arguments | changes))

    def test_ordinary_categories_can_use_shoulder_ads(self):
        for category in (1, 2, 3, 4):
            with self.subTest(category=category):
                self.assertEqual(self.choose(category), "third")

    def test_snipers_heavy_and_unrecognized_categories_keep_native_ads(self):
        for category in (None, 0, 5, 6, 7, 8, True, -1, 1.0, "4", 2**65):
            with self.subTest(category=category):
                self.assertEqual(self.choose(category), "native")

    def test_ineligible_context_keeps_native_ads(self):
        for changes in ({"enabled": False}, {"vehicle": True}, {"pending": True},
                        {"supported": False}, {"foot_mode": "Orbit"},
                        {"foot_mode": "Default"}, {"enabled": 1}):
            with self.subTest(changes=changes):
                self.assertEqual(self.choose(**changes), "native")

    def test_release_is_hip_even_when_category_is_unavailable(self):
        self.assertEqual(self.choose(None, aiming=False), "hip")

    def test_malformed_aim_flag_does_not_authorize_writes(self):
        self.assertEqual(self.choose(aiming=1), "native")


if __name__ == "__main__":
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(PolicyTests))
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    sys.exit(not result.wasSuccessful())
