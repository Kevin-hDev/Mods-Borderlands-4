"""Permanent geometric regressions for thin posts, recovery and wall clearance."""
import math
import random
import unittest

from collision_geometry_fixtures import Geometry, Scene


class Tests(unittest.TestCase):
    def test_return_cannot_jump_across_thin_post_at_any_frame_rate(self):
        for radius in (3, 4):
            settled = []
            for fps in (20, 30, 60, 100, 144, 240):
                scene = Scene(Geometry(pillars=((-193, 10, radius),)))
                scene.query.delta = 1 / fps
                scene.resolver.path.fraction = 0
                values = [scene.frame()[1] for _ in range(2 * fps)]
                self.assertLess(values[-1], 10, (radius, fps, values[-1]))
                self.assertGreater(values[-1], 5)
                self.assertLess(max(values[-fps:]) - min(values[-fps:]), .05)
                settled.append(values[-1])
            self.assertLess(max(settled) - min(settled), .15)

    def test_slow_post_does_not_prolong_natural_occlusion_plus_grace(self):
        for fps in (20, 30, 60, 100, 144, 240):
            geometry = Geometry()
            scene = Scene(geometry)
            scene.query.delta = 1 / fps
            scene.frame()
            hidden = 0
            trace_total = 0
            for frame in range(3 * fps):
                geometry.pillars = ((-193, 60 - frame * 25 / fps, 3),)
                geometry.spheres = geometry.lines = 0
                position = scene.frame()
                trace_total += geometry.spheres + geometry.lines
                hidden += not scene.resolver.visibility.clear(scene.actor, position, (0, 0, 60))
            self.assertLessEqual(hidden / fps, .23 + .2 + 1 / fps, (fps, hidden / fps))
            self.assertLess(trace_total / (3 * fps), 10)

    def test_existing_pillar_is_resolved_immediately_on_entry_and_reentry(self):
        scene = Scene(Geometry(pillars=((-193, 41, 3),)))
        for _ in range(2):
            position = scene.frame()
            self.assertTrue(scene.resolver.visibility.clear(scene.actor, position, (0, 0, 60)))
            scene.resolver.invalidate()

    def test_grace_is_elapsed_time_and_inward_movement_stays_smooth(self):
        for fps in (30, 60, 144, 240):
            scene = Scene(Geometry())
            scene.query.delta = 1 / fps
            scene.frame()
            scene.geometry.pillars = ((-193, 41, 3),)
            first_movement = None
            previous = 53.2
            for frame in range(fps):
                position = scene.frame()[1]
                if first_movement is None and position < 53.2:
                    first_movement = (frame + 1) / fps
                self.assertLessEqual(abs(position - previous), 160 / fps + 1e-6)
                previous = position
            self.assertIsNotNone(first_movement)
            self.assertGreaterEqual(first_movement, .2 - 1e-8)
            self.assertLessEqual(first_movement, .2 + 1 / fps + 1e-8)

    def test_added_offset_rejects_eleven_cm_endpoint_in_detailed_geometry(self):
        for detailed in (False, True):
            geometry = Geometry(planes=(((1, 0, 0), -261),))
            geometry.detailed_only = detailed
            scene = Scene(geometry)
            self.assertEqual(scene.frame(), (-250, 0, 80))

    def test_already_hidden_camera_escapes_smoothly_to_clear_shoulder(self):
        for fps in (30, 60, 144, 240):
            scene = Scene(Geometry())
            scene.query.delta = 1 / fps
            scene.frame()
            scene.resolver.path.fraction = .25
            scene.geometry.pillars = ((-193, 10, 3),)
            position = scene.frame()
            self.assertGreater(position[1], 13.3)
            self.assertLess(position[1], 53.2)
            for _ in range(fps * 2):
                position = scene.frame()
            self.assertTrue(scene.resolver.visibility.clear(scene.actor, position, (0, 0, 60)))

    def test_twelve_cm_boundary_has_one_cm_release_hysteresis(self):
        geometry = Geometry()
        scene = Scene(geometry)
        scene.frame()
        values = []
        for gap in (11.9, 12.1) * 60:
            geometry.planes = (((1, 0, 0), -250 - gap),)
            values.append(scene.frame()[1])
        self.assertEqual(max(values), 0)
        geometry.planes = (((1, 0, 0), -263.1),)
        self.assertGreater(scene.frame()[1], 0)

    def test_open_terrain_returns_to_four_traces_after_contact(self):
        geometry = Geometry(planes=(((0, -1, 0), -25),))
        scene = Scene(geometry)
        scene.frame()
        geometry.planes = ()
        for _ in range(240):
            scene.frame()
        geometry.spheres = geometry.lines = 0
        self.assertEqual(scene.frame()[1], 53.2)
        self.assertEqual(geometry.spheres + geometry.lines, 4)

    def test_random_corners_keep_preferred_margin_on_added_offset(self):
        rng = random.Random(913)
        for detailed in (False, True):
            for _ in range(300):
                gap = rng.uniform(3, 13)
                side = rng.uniform(12.1, 65)
                angle = rng.uniform(-.7, .7)
                normal = (math.sin(angle), -math.cos(angle), 0)
                offset = -250 * normal[0] - side
                geometry = Geometry(planes=(((1, 0, 0), -250-gap), (normal, offset)))
                geometry.detailed_only = detailed
                scene = Scene(geometry)
                position = scene.frame()
                if position != (-250, 0, 80):
                    margin = sum(a*b for a, b in zip(normal, position)) - offset
                    # Approved 1 mm contact budget, not a reduction of the camera's 10 cm physical radius.
                    self.assertGreaterEqual(margin, 11.9 - 1e-8)
                    self.assertGreaterEqual(position[0] + 250 + gap, 11.9 - 1e-8)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
