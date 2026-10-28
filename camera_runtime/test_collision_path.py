"""Camera points and segments from the game are checked before any sweep reads them."""
import math
import unittest

from apex_camera_runtime.collision_config import MAX_COORDINATE, MAX_LENGTH
from apex_camera_runtime.collision_path import point, segment


class Tests(unittest.TestCase):
    def test_a_point_comes_back_as_three_floats(self):
        self.assertEqual(point([1, 2, 3]), (1.0, 2.0, 3.0))
        self.assertEqual(point((-MAX_COORDINATE, 0, MAX_COORDINATE)), (-MAX_COORDINATE, 0.0, MAX_COORDINATE))

    def test_a_malformed_or_unbounded_point_is_refused(self):
        for value in ((1, 2), (1, 2, 3, 4), "abc", None, (math.nan, 0, 0), (0, math.inf, 0),
                      (0, 0, MAX_COORDINATE * 1.01)):
            with self.subTest(value=value), self.assertRaises(ValueError):
                point(value)

    def test_a_segment_gives_its_ends_and_length(self):
        self.assertEqual(segment((0, 0, 0), (0, 30, 40)), ((0.0, 0.0, 0.0), (0.0, 30.0, 40.0), 50.0))

    def test_an_empty_or_too_long_segment_is_refused(self):
        for end in ((0, 0, 0), (MAX_LENGTH + 1, 0, 0)):
            with self.subTest(end=end), self.assertRaises(ValueError):
                segment((0, 0, 0), end)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
