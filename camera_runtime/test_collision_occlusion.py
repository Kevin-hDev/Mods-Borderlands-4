"""Wide visual obstacles have a bounded return; passing thin posts keep their grace."""
import unittest
from itertools import product

from collision_geometry_fixtures import Geometry, Scene


class Tests(unittest.TestCase):
    def test_wide_obstacle_returns_upper_body_within_point_eight_seconds(self):
        for fps in (20, 30, 60, 100, 144, 240):
            for offset, corner, detailed in product((50, 68.2), (False, True), (False, True)):
                with self.subTest(fps=fps, offset=offset, corner=corner, detailed=detailed):
                    geometry = Geometry()
                    geometry.detailed_only = detailed
                    scene = Scene(geometry)
                    scene.query.delta = 1 / fps
                    scene.query.desired[:] = (-250, offset, 80)
                    scene.frame()
                    if corner:
                        geometry.walls = (((-193, 1), (-193, 200)),)
                    else:
                        geometry.pillars = ((-193, 41, 40),)
                    first_visible = None
                    for frame in range(fps):
                        position = scene.frame()
                        if scene.resolver.visibility.clear(scene.actor, position, (0, 0, 60)):
                            first_visible = (frame + 1) / fps
                            break
                    self.assertIsNotNone(first_visible)
                    self.assertLessEqual(first_visible, .8)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
