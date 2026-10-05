"""A previous wall latch must not prevent a safe shortened shoulder from returning."""
import math
import unittest
from itertools import product

from collision_geometry_fixtures import Geometry, Scene


class Tests(unittest.TestCase):
    def test_corridor_releases_after_native_camera_leaves_rear_wall(self):
        for fps, behind, side, detailed in product((20, 30, 60, 100, 144, 240),
                                                   (3, 8, 11.9), (30, 40, 60, 66), (False, True)):
            with self.subTest(fps=fps, behind=behind, side=side, detailed=detailed):
                geometry = Geometry(planes=(((1, 0, 0), -250 - behind), ((0, -1, 0), -side)))
                geometry.detailed_only = detailed
                scene = Scene(geometry)
                scene.query.delta = 1 / fps
                self.assertEqual(scene.frame()[1], 0)
                geometry.planes = (((0, -1, 0), -side),)
                limit = min(53.2, side - 12)
                first = scene.frame()[1]
                self.assertGreater(first, 0)
                self.assertLess(first, limit)
                for _ in range(2 * fps):
                    position = scene.frame()
                    self.assertLessEqual(position[1], limit + 1e-8)
                    self.assertGreaterEqual(side - position[1], 12 - 1e-8)
                self.assertAlmostEqual(position[1], limit, places=5)
                self.assertFalse(scene.resolver.margin_blocked)

    def test_initial_cutoff_is_twelve_not_thirteen_on_swept_target(self):
        sine = 4.6 / 53.2
        normal = (math.sqrt(1 - sine * sine), sine, 0)
        offset = -250 * normal[0] - 8
        for detailed in (False, True):
            geometry = Geometry(planes=((normal, offset),))
            geometry.detailed_only = detailed
            scene = Scene(geometry)
            position = scene.frame()
            self.assertAlmostEqual(sum(a * n for a, n in zip(position, normal)) - offset, 12.6)
            self.assertEqual(position[1], 53.2)
            self.assertFalse(scene.resolver.margin_blocked)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
