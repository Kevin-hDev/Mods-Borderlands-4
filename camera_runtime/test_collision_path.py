"""Retraction is immediate; recovery is smooth, frame-rate independent and bounded."""
import importlib.util
import math
import unittest


class Tests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("apex_camera_runtime.collision_path"),
                             "Continuous collision path solver is missing")
        from apex_camera_runtime.collision_path import CollisionPath
        self.path = CollisionPath()

    def test_wall_retracts_immediately_and_clearance_does_not_pop_back(self):
        self.assertEqual(self.path.resolve((0, 0, 0), (100, 0, 0), 40, .016), (40, 0, 0))
        returned = self.path.resolve((0, 0, 0), (100, 0, 0), 100, .016)
        self.assertGreater(returned[0], 40)
        self.assertLess(returned[0], 100)
        self.assertEqual(self.path.resolve((0, 0, 0), (100, 0, 0), 20, .016), (20, 0, 0))

    def test_recovery_matches_at_30_60_and_120_fps(self):
        values = []
        for fps in (30, 60, 120):
            self.path.reset()
            self.path.resolve((0, 0, 0), (100, 0, 0), 40, 0)
            for _ in range(fps):
                position = self.path.resolve((0, 0, 0), (100, 0, 0), 100, 1 / fps)
            values.append(position[0])
        self.assertAlmostEqual(values[0], values[1], places=9)
        self.assertAlmostEqual(values[1], values[2], places=9)

    def test_current_frame_anchor_and_direction_are_used_during_recovery(self):
        self.path.resolve((0, 0, 0), (100, 0, 0), 40, .016)
        self.assertEqual(self.path.resolve((10, 0, 0), (10, 100, 0), 20, .016), (10, 20, 0))

    def test_clearance_never_exceeds_the_swept_prefix(self):
        for distance in (25, 24, 30, 15, 100, 7):
            point = self.path.resolve((0, 0, 0), (60, 80, 0), distance, .016)
            self.assertLessEqual(math.dist((0, 0, 0), point), distance + 1e-9)

    def test_invalid_geometry_does_not_advance_recovery(self):
        for anchor, desired, distance, delta in (
            ((math.nan, 0, 0), (100, 0, 0), 50, .016),
            ((0, 0, 0), (100, 0, 0), 101, .016),
            ((0, 0, 0), (100, 0, 0), 40, -1),
        ):
            with self.assertRaises(ValueError):
                self.path.resolve(anchor, desired, distance, delta)
        self.assertEqual(self.path.resolve((0, 0, 0), (100, 0, 0), 100, .016), (100, 0, 0))


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
