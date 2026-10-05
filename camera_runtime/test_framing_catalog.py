"""Saved framing rejects invalid percentages without silently diluting presets."""
import importlib.util
import unittest


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("apex_camera_runtime.framing_catalog"),
                             "framing catalog not implemented")
        from apex_camera_runtime import framing_catalog
        self.catalog = framing_catalog

    def test_defaults_and_exact_approved_presets(self):
        expected = (("zoom", 15, (0, 15, 25)), ("horizontal", 10, (0, 10, 20)),
                    ("height", 0, (0, 10, -10)))
        for key, default, presets in expected:
            with self.subTest(key=key):
                group = self.catalog.group(key)
                self.assertEqual(group.default, default)
                self.assertEqual(tuple(value for _, value in group.presets), presets)
                self.assertTrue(all(group.valid(value) for value in presets))

    def test_custom_ranges_are_integer_steps_and_not_smaller_than_the_reference(self):
        for key in ("zoom", "horizontal"):
            group = self.catalog.group(key)
            for value in (0, 1, 49, 50):
                self.assertTrue(group.valid(value))
            for bad in (-1, 51, True, 15.5, "15", None, float("nan"), float("inf")):
                self.assertFalse(group.valid(bad))
        height = self.catalog.group("height")
        for value in (-50, -10, 0, 10, 50):
            self.assertTrue(height.valid(value))
        self.assertFalse(height.valid(-51))
        self.assertFalse(height.valid(51))

    def test_unknown_group_cannot_create_an_unbounded_option(self):
        for key in ("unknown", "../zoom", "zoom" * 100, None, True):
            with self.assertRaises(ValueError):
                self.catalog.group(key)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
