"""An initial narrow volume cannot certify a later wall's full clearance."""
import unittest
import math
from types import SimpleNamespace as NS

from collision_geometry_fixtures import Geometry, Scene
from apex_camera_runtime.collision_sweep import SphereSweep


class Tests(unittest.TestCase):
    def test_close_corner_never_publishes_less_than_twelve_units_from_side_wall(self):
        for behind in (2.9, 3.1, 4, 8):
            with self.subTest(behind=behind):
                scene = Scene(Geometry(planes=(((1, 0, 0), -250 - behind), ((0, -1, 0), -40))))
                point = scene.frame()
                self.assertLessEqual(point[1], 28)

    def test_initially_overlapping_full_volume_is_not_claimed_safe_at_endpoint(self):
        scene = Scene(Geometry(planes=(((1, 0, 0), -254),)))
        self.assertEqual(scene.frame(), (-250, 0, 80))

    def test_two_millimeter_initial_wall_change_does_not_flip_camera_to_full_offset(self):
        geometry = Geometry()
        scene = Scene(geometry)
        values = []
        for behind in (2.9, 3.1) * 30:
            geometry.planes = (((1, 0, 0), -250 - behind),)
            values.append(scene.frame()[1])
        self.assertLess(max(values) - min(values), .1)

    def test_wall_safety_never_waits_for_visual_delay_or_smooth_retraction(self):
        geometry = Geometry()
        scene = Scene(geometry)
        scene.frame()
        geometry.planes = (((0, -1, 0), -25),)
        self.assertAlmostEqual(scene.frame()[1], 13)

    def test_raised_shoulder_preserves_twelve_units_normal_to_side_wall(self):
        scene = Scene(Geometry(planes=(((0, -1, 0), -40),)))
        scene.query.desired[:] = (-250, 53.2, 130)
        position = scene.frame()
        self.assertLessEqual(position[1], 28 + 1e-9)
        self.assertEqual(position[0], -250)

    def test_new_wall_clips_immediately_during_visual_recentring(self):
        geometry = Geometry(pillars=((-193, 41, 3),))
        scene = Scene(geometry)
        for _ in range(45):
            scene.frame()
        self.assertGreater(scene.frame()[1], 40)
        geometry.planes = (((0, -1, 0), -25),)
        position = scene.frame()
        self.assertAlmostEqual(position[1], 13)
        self.assertEqual((position[0], position[2]), (-250, 80))

    def test_repeated_zero_depth_never_certifies_a_whole_segment_as_safe(self):
        sdk = NS(make_struct=lambda name, **values: NS(**values))
        unknown = NS(SphereTraceSingle=lambda *args: (True, NS(Distance=0,
                     bStartPenetrating=True, PenetrationDepth=0)))
        self.assertEqual(SphereSweep(unknown, sdk).distance(object(), (0, 0, 0), (0, 40, 0)), 0)

    def test_finite_wall_preserves_full_volume_on_both_geometry_channels(self):
        for detailed in (False, True):
            geometry = Geometry(walls=(((-270, 25), (-230, 25)),))
            geometry.detailed_only = detailed
            self.assertAlmostEqual(Scene(geometry).frame()[1], 13)

    def test_finite_wall_corner_hits_rounded_volume_without_infinite_wall_extension(self):
        corner = Scene(Geometry(walls=(((-240, 25), (-200, 25)),)))
        self.assertAlmostEqual(corner.frame()[1], 25 - math.sqrt(44))
        missed = Scene(Geometry(walls=(((-230, 25), (-200, 25)),)))
        self.assertEqual(missed.frame()[1], 53.2)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
