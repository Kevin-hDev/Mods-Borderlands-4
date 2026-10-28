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
        expected = (("zoom", 15, (0, 15, 25)), ("horizontal", 10, (-40, 10, 60)),
                    ("height", 0, (-40, 0, 40)))
        for key, default, presets in expected:
            with self.subTest(key=key):
                group = self.catalog.group(key)
                self.assertEqual(group.default, default)
                self.assertEqual(tuple(value for _, value in group.presets), presets)
                self.assertTrue(all(group.valid(value) for value in presets))

    def test_custom_ranges_are_integer_steps_and_the_zoom_not_smaller_than_the_reference(self):
        # The zoom never goes below the game's; spacing and height go both ways (Kevin, 2026-10-11).
        for key, low, high in (("zoom", 0, 50), ("horizontal", -60, 120), ("height", -240, 100)):
            group = self.catalog.group(key)
            for value in (low, low + 1, 0, high - 1, high):
                self.assertTrue(group.valid(value))
            for bad in (low - 1, high + 1, True, 15.5, "15", None, float("nan"), float("inf")):
                self.assertFalse(group.valid(bad))

    def test_unknown_group_cannot_create_an_unbounded_option(self):
        for key in ("unknown", "../zoom", "zoom" * 100, None, True):
            with self.assertRaises(ValueError):
                self.catalog.group(key)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
