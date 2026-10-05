"""Native clearance may be low; recovery must remain safe and independent of FPS."""
import math
import unittest
from itertools import product

from collision_geometry_fixtures import Geometry, Scene


class Tests(unittest.TestCase):
    def test_reduced_departure_does_not_recheck_known_blocked_native_anchor(self):
        geometry = Geometry(planes=(((1, 0, 0), -253),))
        scene = Scene(geometry)
        for _ in range(3):
            geometry.spheres = geometry.lines = 0
            self.assertEqual(scene.frame(), (-250, 0, 80))
            self.assertTrue(scene.resolver.margin_blocked)
            self.assertEqual(geometry.lines, 0)
            self.assertLessEqual(geometry.spheres, 6)

    def test_blocked_wall_skips_visibility_and_bounds_contact_proof_queries(self):
        for gap, detailed, side, pillar in product((3, 8, 11.9), (False, True), (None, 2, 40), (False, True)):
            with self.subTest(gap=gap, detailed=detailed, side=side, pillar=pillar):
                planes = (((1, 0, 0), -250 - gap),)
                if side is not None:
                    planes += (((0, -1, 0), -side),)
                geometry = Geometry(planes=planes, pillars=((-193, 41, 3),) if pillar else ())
                geometry.detailed_only = detailed
                scene = Scene(geometry)
                for _ in range(3):
                    geometry.spheres = geometry.lines = 0
                    self.assertEqual(scene.frame(), (-250, 0, 80))
                    self.assertEqual(geometry.lines, 0)
                    # Two extra endpoint proofs are necessary when zero depth cannot certify free space.
                    self.assertLessEqual(geometry.spheres, 10)

    def test_angled_wall_releases_toward_clear_target_at_every_frame_rate(self):
        for angle in (5, 10, 20, 30):
            values = []
            normal = (math.cos(math.radians(angle)), math.sin(math.radians(angle)), 0)
            offset = -250 * normal[0] - 11
            for fps in (20, 30, 60, 100, 144, 240):
                for detailed in (False, True):
                    geometry = Geometry(planes=(((1, 0, 0), -261),))
                    geometry.detailed_only = detailed
                    scene = Scene(geometry)
                    scene.query.delta = 1 / fps
                    self.assertEqual(scene.frame()[1], 0)
                    geometry.planes = ((normal, offset),)
                    position = scene.frame()
                    self.assertGreater(position[1], 0, (angle, fps, detailed))
                    # The native camera starts at 11: the early return cannot promise 12.
                    for _ in range(fps // 2 - 1):
                        clearance = sum(a * n for a, n in zip(position, normal)) - offset
                        self.assertGreaterEqual(clearance, 11 - 1e-6)
                        position = scene.frame()
                    values.append(position[1])
                    self.assertGreater(position[1], 53)
            self.assertLess(max(values) - min(values), 1e-6)

    def test_release_waits_for_full_one_cm_hysteresis_on_target(self):
        geometry = Geometry(planes=(((1, 0, 0), -261.9),))
        scene = Scene(geometry)
        self.assertEqual(scene.frame()[1], 0)
        geometry.planes = (((1, 0, 0), -262.6),)
        self.assertEqual(scene.frame()[1], 0)
        self.assertTrue(scene.resolver.margin_blocked)
        geometry.planes = (((1, 0, 0), -263.1),)
        self.assertGreater(scene.frame()[1], 0)

    def test_invalidate_discards_margin_latch_for_new_character_or_map(self):
        geometry = Geometry(planes=(((1, 0, 0), -261),))
        scene = Scene(geometry)
        self.assertEqual(scene.frame()[1], 0)
        scene.resolver.invalidate()
        geometry.planes = (((1, 0, 0), -262.6),)
        self.assertEqual(scene.frame()[1], 53.2)
        self.assertFalse(scene.resolver.margin_blocked)

    def test_character_loss_clears_wall_latch_before_next_owner(self):
        scene = Scene(Geometry(planes=(((1, 0, 0), -261),)))
        self.assertEqual(scene.frame()[1], 0)
        scene.pc.OakCharacter = None
        with self.assertRaises(AssertionError):
            scene.frame()
        self.assertFalse(scene.resolver.margin_blocked)
        self.assertFalse(scene.resolver.path.initialized)

    def test_orbit_takeover_clears_wall_latch_before_third_person_returns(self):
        geometry = Geometry(planes=(((1, 0, 0), -261),))
        scene = Scene(geometry)
        self.assertEqual(scene.frame()[1], 0)
        scene.manager.GetActorCameraMode = lambda _: 'Orbit'
        with self.assertRaises(AssertionError):
            scene.frame()
        self.assertFalse(scene.resolver.margin_blocked)
        scene.manager.GetActorCameraMode = lambda _: 'ThirdPerson'
        geometry.planes = (((1, 0, 0), -262.6),)
        self.assertEqual(scene.frame()[1], 53.2)

    def test_native_low_clearance_cannot_tunnel_through_intermediate_post(self):
        normal = (math.cos(math.radians(10)), math.sin(math.radians(10)), 0)
        offset = -250 * normal[0] - 11
        for detailed in (False, True):
            geometry = Geometry(planes=((normal, offset),), pillars=((-250, 26, 3),))
            geometry.detailed_only = detailed
            scene = Scene(geometry)
            for _ in range(120):
                position = scene.frame()
                self.assertLess(position[1], 26)
                self.assertGreaterEqual(math.hypot(position[0] + 250, position[1] - 26) - 3,
                                        11 - 1e-6)

    def test_secondary_wall_clips_immediately_while_leaving_low_native_margin(self):
        normal = (math.cos(math.radians(10)), math.sin(math.radians(10)), 0)
        offset = -250 * normal[0] - 11
        for fps in (20, 60, 144, 240):
            geometry = Geometry(planes=((normal, offset),))
            scene = Scene(geometry)
            scene.query.delta = 1 / fps
            for _ in range(fps):
                scene.frame()
            geometry.planes = ((normal, offset), ((0, -1, 0), -25))
            position = scene.frame()
            self.assertLessEqual(position[1], 13 + 1e-6)

    def test_reduced_sweep_preserves_native_clearance_between_clear_endpoints(self):
        normal = (math.cos(math.radians(10)), math.sin(math.radians(10)), 0)
        offset = -250 * normal[0] - 11
        for fps in (20, 30, 60, 100, 144, 240):
            geometry = Geometry(planes=((normal, offset),), pillars=((-263.5, 26, 3),))
            scene = Scene(geometry)
            scene.query.delta = 1 / fps
            for _ in range(fps):
                position = scene.frame()
                self.assertLess(position[1], 26, (fps, position))
                clearance = math.hypot(position[0] + 263.5, position[1] - 26) - 3
                self.assertGreaterEqual(clearance, 11 - 1e-6, (fps, position))

    def test_margin_release_from_hidden_native_view_returns_without_entry_snap(self):
        normal = (math.cos(math.radians(10)), math.sin(math.radians(10)), 0)
        offset = -250 * normal[0] - 11
        settled = []
        for fps in (20, 30, 60, 100, 144, 240):
            geometry = Geometry(planes=(((1, 0, 0), -261),), pillars=((-193, 0, 3),))
            scene = Scene(geometry)
            scene.query.delta = 1 / fps
            self.assertEqual(scene.frame()[1], 0)
            geometry.planes = ((normal, offset),)
            position = scene.frame()
            self.assertGreater(position[1], 0)
            self.assertLess(position[1], 53.2, fps)
            for _ in range(fps // 2 - 1):
                next_position = scene.frame()
                self.assertGreaterEqual(next_position[1], position[1])
                position = next_position
            settled.append(position[1])
            self.assertGreater(position[1], 53)
        self.assertLess(max(settled) - min(settled), 1e-6)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
