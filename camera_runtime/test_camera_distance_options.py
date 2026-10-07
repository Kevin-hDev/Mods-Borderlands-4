"""The key's saved choice is one of the three; the close and far distances are set in metres and read in
centimetres; a hand-edited value reads as its default; a failed save keeps the previous choice."""

import sys
import unittest
from types import SimpleNamespace as NS


class Option:
    def __init__(self, identifier, value, min_value=None, max_value=None, *args, **kwargs):
        self.identifier, self.value, self.kwargs = identifier, value, kwargs
        self.min_value, self.max_value = min_value, max_value


sys.modules["mods_base"] = NS(SliderOption=Option, BoolOption=Option)

from apex_camera_runtime.camera_distance import CLOSE, DISTANCES, FAR, NORMAL, NORMAL_CM  # noqa: E402
from apex_camera_runtime.camera_distance_options import CameraDistanceOptions  # noqa: E402


class OptionTests(unittest.TestCase):
    def test_saved_choice_and_validation(self):
        distance = CameraDistanceOptions()
        distance.option.mod = NS(save_settings=lambda: None)
        self.assertEqual(distance.option.identifier, "camera_distance")
        self.assertTrue(distance.option.kwargs["is_hidden"])
        self.assertEqual(distance.index(), NORMAL)
        for bad in (True, 1.0, "far", -1, 3, None):
            distance.option.value = bad
            self.assertEqual(distance.index(), NORMAL)
            with self.assertRaises(ValueError):
                distance.save(bad)
        distance.save(FAR)
        self.assertEqual(distance.index(), FAR)

        def fail():
            raise RuntimeError("save refused")
        distance.option.mod.save_settings = fail
        with self.assertRaises(RuntimeError):
            distance.save(CLOSE)
        self.assertEqual(distance.index(), FAR)

    def test_close_and_far_are_shown_in_metres_and_stay_on_their_side_of_normal(self):
        distance = CameraDistanceOptions()
        self.assertEqual([option.identifier for option in distance.options],
                         ["camera_distance_close", "camera_distance_far"])
        self.assertFalse(any(option.kwargs.get("is_hidden") for option in distance.options))
        self.assertEqual(distance.distances(), DISTANCES)
        self.assertLess(distance.close.max_value * 100, NORMAL_CM)
        self.assertGreater(distance.far.min_value * 100, NORMAL_CM)
        distance.close.value, distance.far.value = 1.25, 4.5
        self.assertEqual(distance.distances(), (125.0, NORMAL_CM, 450.0))
        distance.close.value, distance.far.value = 9.0, 0.5
        self.assertEqual(distance.distances(), (distance.close.max_value * 100, NORMAL_CM,
                                                distance.far.min_value * 100))
        distance.close.value, distance.far.value = "1.5", float("nan")
        self.assertEqual(distance.distances(), DISTANCES)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
