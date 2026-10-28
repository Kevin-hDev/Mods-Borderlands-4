"""Saved distance is bounded; failed persistence restores the previous choice."""

import importlib.util
import sys
import unittest
from types import SimpleNamespace as NS


class Option:
    def __init__(self, identifier, value, *args, **kwargs):
        self.identifier, self.value = identifier, value


sys.modules["mods_base"] = NS(SliderOption=Option)


class OptionTests(unittest.TestCase):
    def test_saved_distance_and_validation(self):
        self.assertIsNotNone(importlib.util.find_spec("apex_camera_runtime.orbit_zoom_options"),
                             "saved zoom option missing")
        from apex_camera_runtime.orbit_zoom_options import OrbitZoomOptions
        zoom = OrbitZoomOptions()
        zoom.option.mod = NS(save_settings=lambda: None)
        self.assertEqual(zoom.distance(), 300)
        for bad in (True, "75", float("nan"), float("inf"), 74, 601):
            zoom.option.value = bad
            self.assertEqual(zoom.distance(), 300)
            with self.assertRaises(ValueError):
                zoom.save(bad)
        zoom.save(75)
        self.assertEqual(zoom.distance(), 75)
        def fail():
            raise RuntimeError("save refused")
        zoom.option.mod.save_settings = fail
        with self.assertRaises(RuntimeError):
            zoom.save(600)
        self.assertEqual(zoom.distance(), 75)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
