"""Fresh upper-body sightlines cannot force an infinite pillar oscillation."""
import unittest
from types import SimpleNamespace as NS

from collision_geometry_fixtures import Geometry, Scene
from apex_camera_runtime.collision_visibility import Visibility


class Tests(unittest.TestCase):
    def test_stationary_pillar_cannot_repeat_recovery_and_reset(self):
        scene = Scene(Geometry(pillars=((-193, 10, 3),)))
        scene.resolver.path.fraction = 0
        values = [scene.frame()[1] for _ in range(180)]
        self.assertGreater(values[-1], 5)
        self.assertLess(max(values[120:]) - min(values[120:]), .05)
        self.assertLess(max(abs(b - a) for a, b in zip(values, values[1:])), 10)

    def test_final_recovery_check_prevents_crossing_a_persistent_hidden_region(self):
        scene = Scene(Geometry(pillars=((-193, 10, 4),)))
        scene.resolver.path.fraction = 0
        values = [scene.frame()[1] for _ in range(180)]
        self.assertGreater(values[-1], 5)
        self.assertLess(values[-1], 8.5)
        self.assertLess(max(values[120:]) - min(values[120:]), .05)

    def test_moving_pillar_does_not_create_repeated_large_jumps(self):
        geometry = Geometry()
        scene = Scene(geometry)
        values = []
        for frame in range(180):
            geometry.pillars = ((-193, -20 + frame * 100 / 60, 3),)
            position = scene.frame()
            self.assertEqual((position[0], position[2]), (-250, 80))
            values.append(position[1])
        self.assertLess(max(abs(b - a) for a, b in zip(values, values[1:])), 10)

    def test_brief_visual_obstacle_does_not_recenter_before_point_two_seconds(self):
        geometry = Geometry()
        scene = Scene(geometry)
        self.assertEqual(scene.frame()[1], 53.2)
        geometry.pillars = ((-193, 41, 3),)
        for _ in range(10):
            self.assertEqual(scene.frame()[1], 53.2)
        geometry.pillars = ()
        self.assertEqual(scene.frame()[1], 53.2)

    def test_persistent_visibility_retraction_is_smooth_in_both_directions(self):
        geometry = Geometry()
        scene = Scene(geometry)
        scene.frame()
        geometry.pillars = ((-193, 41, 3),)
        values = [scene.frame()[1] for _ in range(100)]
        self.assertLess(values[-1], 49.3)
        self.assertLess(max(abs(b - a) for a, b in zip([53.2] + values, values)), 3)
        geometry.pillars = ()
        returned = scene.frame()[1]
        self.assertGreater(returned, values[-1])
        self.assertLess(returned, 53.2)

    def test_clear_exact_candidate_does_not_repeat_sightline_checks(self):
        geometry = Geometry()
        scene = Scene(geometry)
        scene.frame()
        self.assertEqual(geometry.lines, 2)

    def test_detailed_geometry_and_original_upper_body_point_are_checked(self):
        geometry = Geometry(pillars=((-193, 41, 3),))
        geometry.detailed_only = True
        scene = Scene(geometry)
        for _ in range(90):
            point = scene.frame()
        self.assertLess(point[1], 49.3)
        self.assertGreater(point[1], 40)

    def test_hidden_native_view_cannot_certify_an_unchecked_prefix(self):
        geometry = Geometry(pillars=((-193, 0, 3), (-193, 41, 3)))
        scene = Scene(geometry)
        for _ in range(90):
            point = scene.frame()
        self.assertLess(point[1], .01)

    def test_missing_character_invalidates_visual_recovery(self):
        scene = Scene(Geometry())
        scene.resolver.path.fraction = .4
        scene.pc.OakCharacter = None
        with self.assertRaises(AssertionError):
            scene.frame()
        self.assertEqual(scene.resolver.path.fraction, 1)

    def test_moving_current_segment_never_reuses_an_old_world_position(self):
        scene = Scene(Geometry(pillars=((-193, 10, 3),)))
        scene.resolver.path.fraction = 0
        for _ in range(90):
            scene.frame()
        scene.query.before[:] = (-500, 100, 80)
        scene.query.desired[:] = (-500, 153.2, 80)
        position = scene.frame()
        self.assertEqual((position[0], position[2]), (-500, 80))
        self.assertGreaterEqual(position[1], 100)
        self.assertLessEqual(position[1], 153.2)

    def test_visibility_target_rejects_unknown_body_dimensions(self):
        actor = NS(K2_GetActorLocation=lambda: NS(X=0, Y=0, Z=0),
                   CapsuleComponent=NS(GetScaledCapsuleHalfHeight=lambda: float('nan')))
        with self.assertRaises(ValueError):
            Visibility.target(actor)

    def test_upper_body_below_camera_cover_is_not_replaced_by_camera_height(self):
        scene = Scene(Geometry(planes=(((0, 0, 1), 65),)))
        for _ in range(100):
            position = scene.frame()
        self.assertLess(position[1], .01)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
