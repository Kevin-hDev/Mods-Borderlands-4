"""Initial contact is rechecked, never mistaken for a certified free full segment."""
import math
import unittest
from itertools import product
from types import SimpleNamespace as NS

from collision_contact_fixtures import ContactGeometry, MovingOnlyGeometry, UnknownOverlapGeometry
from collision_geometry_fixtures import Geometry, Scene
from apex_camera_runtime.collision_sweep import SphereSweep


class Tests(unittest.TestCase):
    def test_zero_length_blind_engine_cannot_certify_an_unsafe_corner(self):
        for side, detailed in product((-1, 1), (False, True)):
            geometry = MovingOnlyGeometry(planes=(((1, 0, 0), -253), ((0, -side, 0), -40)))
            geometry.detailed_only = detailed
            scene = Scene(geometry)
            scene.query.desired[1] = side * 53.2
            for _ in range(6):
                self.assertEqual(scene.frame(), (-250, 0, 80))
                self.assertEqual(scene.resolver.diagnostics.errors, 0)

    def test_unknown_endpoint_depth_cannot_publish_camera_inside_wall_margin(self):
        for gap, side, detailed in product((3, 8, 11.8), (None, 40), (False, True)):
            with self.subTest(gap=gap, side=side, detailed=detailed):
                planes = (((1, 0, 0), -250 - gap),)
                if side is not None:
                    planes += (((0, -1, 0), -side),)
                geometry = UnknownOverlapGeometry(planes=planes)
                geometry.detailed_only = detailed
                scene = Scene(geometry)
                for _ in range(6):
                    self.assertEqual(scene.frame(), (-250, 0, 80))
                self.assertEqual(scene.resolver.diagnostics.errors, 0)

    def test_rounded_departure_recovers_at_all_cadences_and_both_geometry_modes(self):
        for angle, band, fps, detailed in product((5, 10, 20, 30), (.0001, .005, .02, .075),
                                                 (20, 30, 60, 100, 144, 240), (False, True)):
            with self.subTest(angle=angle, band=band, fps=fps, detailed=detailed):
                normal = (math.cos(math.radians(angle)), math.sin(math.radians(angle)), 0)
                geometry = ContactGeometry(planes=(((1, 0, 0), -261),), band=band)
                geometry.detailed_only = detailed
                scene = Scene(geometry)
                scene.query.delta = 1 / fps
                self.assertEqual(scene.frame()[1], 0)
                offset = -250 * normal[0] - 11
                geometry.planes = ((normal, offset),)
                first = scene.frame()[1]
                self.assertGreater(first, 0)
                self.assertLess(first, 53.2)
                for _ in range(fps):
                    position = scene.frame()
                    self.assertGreaterEqual(sum(a * n for a, n in zip(position, normal)) - offset,
                                            10.9 - 1e-8)
                self.assertGreater(position[1], 53)
                self.assertEqual(scene.resolver.diagnostics.errors, 0)

    def test_zero_and_tiny_contacts_allow_angled_recovery_without_errors(self):
        normal = (math.cos(math.radians(10)), math.sin(math.radians(10)), 0)
        offset = -250 * normal[0] - 11
        for fps, depth, penetrating, detailed in product((20, 30, 60, 100, 144, 240),
                                                         (0, 1e-9), (False, True), (False, True)):
            with self.subTest(fps=fps, depth=depth, penetrating=penetrating, detailed=detailed):
                geometry = ContactGeometry(planes=(((1, 0, 0), -261),), depth=depth,
                                           penetrating=penetrating)
                geometry.detailed_only = detailed
                scene = Scene(geometry)
                scene.query.delta = 1 / fps
                self.assertEqual(scene.frame()[1], 0)
                geometry.planes = ((normal, offset),)
                first = scene.frame()[1]
                self.assertGreater(first, 0)
                self.assertLess(first, 53.2)
                for _ in range(fps):
                    position = scene.frame()
                    self.assertGreaterEqual(sum(a * n for a, n in zip(position, normal)) - offset,
                                            11 - 1e-6)
                self.assertGreater(position[1], 53)
                self.assertEqual(scene.resolver.diagnostics.errors, 0)

    def test_contact_cannot_hide_secondary_wall_or_intermediate_pillar(self):
        normal = (math.cos(math.radians(10)), math.sin(math.radians(10)), 0)
        offset = -250 * normal[0] - 11
        for depth, detailed, pillar in product((0, 1e-9), (False, True), (False, True)):
            planes = ((normal, offset),) if pillar else ((normal, offset), ((0, -1, 0), -40))
            geometry = ContactGeometry(planes=planes, pillars=((-263.5, 26, 3),) if pillar else (),
                                       depth=depth)
            geometry.detailed_only = detailed
            scene = Scene(geometry)
            for _ in range(120):
                position = scene.frame()
                self.assertEqual(position, (-250, 0, 80))
                self.assertEqual(scene.resolver.diagnostics.errors, 0)

    def test_full_margin_tangent_and_outward_contacts_do_not_pin_camera(self):
        for depth, penetrating, normal in product((0, 1e-9), (False, True), ((1, 0, 0), (0, 1, 0))):
            offset = -250 * normal[0] - 12
            scene = Scene(ContactGeometry(planes=((normal, offset),), depth=depth,
                                          penetrating=penetrating))
            self.assertEqual(scene.frame()[1], 53.2)
            self.assertEqual(scene.resolver.diagnostics.errors, 0)

    def test_touching_departure_toward_wall_remains_physically_blocked(self):
        for depth, penetrating in product((0, 1e-9), (False, True)):
            scene = Scene(ContactGeometry(planes=(((0, -1, 0), -12),), depth=depth,
                                          penetrating=penetrating))
            for _ in range(4):
                self.assertEqual(scene.frame(), (-250, 0, 80))
                self.assertEqual(scene.resolver.diagnostics.errors, 0)

    def test_two_rechecks_negotiate_distinct_departure_surfaces_and_later_obstacle(self):
        sdk = NS(make_struct=lambda name, **values: NS(**values))
        geometry = Geometry(planes=(((1, 0, 0), -258), ((0, 1, 0), -5), ((0, -1, 0), -40)))
        distance = SphereSweep(geometry, sdk).distance(object(), (-250, 0, 80), (-250, 53.2, 80))
        self.assertGreater(distance, 34)
        # The native narrowest surface is at 5 cm; contact separation may spend at most 1 mm.
        self.assertLessEqual(distance, 35.1 + 1e-8)
        self.assertEqual(geometry.spheres, 6)

    def test_tangent_departure_keeps_secondary_margin_with_one_mm_contact_budget(self):
        for detailed in (False, True):
            geometry = ContactGeometry(planes=(((1, 0, 0), -262), ((0, -1, 0), -40)))
            geometry.detailed_only = detailed
            scene = Scene(geometry)
            position = scene.frame()
            self.assertGreater(position[1], 27.99)
            self.assertGreaterEqual(40 - position[1], 11.9 - 1e-8)
            self.assertLessEqual(position[1], 28.1 + 1e-8)
            self.assertEqual(scene.resolver.diagnostics.errors, 0)

    def test_persistent_contact_after_bounded_rechecks_retains_native_without_errors(self):
        normal = (math.cos(math.radians(10)), math.sin(math.radians(10)), 0)
        offset = -250 * normal[0] - 11
        for depth, detailed in product((0, 1e-9), (False, True)):
            geometry = ContactGeometry(planes=((normal, offset),), depth=depth, band=.1001)
            geometry.detailed_only = detailed
            scene = Scene(geometry)
            for _ in range(3):
                geometry.spheres = geometry.lines = 0
                self.assertEqual(scene.frame(), (-250, 0, 80))
                self.assertEqual(scene.resolver.diagnostics.errors, 0)
                self.assertEqual(geometry.lines, 0)
                # Endpoint contact now needs a second real query instead of trusting zero depth.
                self.assertLessEqual(geometry.spheres, 10)

    def test_rounded_tangent_corner_keeps_camera_volume_safe_on_both_shoulders(self):
        for side, band, detailed in product((-1, 1), (.005, .02, .075, .1001), (False, True)):
            with self.subTest(side=side, band=band, detailed=detailed):
                geometry = ContactGeometry(planes=(((1, 0, 0), -262), ((0, -side, 0), -40)),
                                           band=band)
                geometry.detailed_only = detailed
                scene = Scene(geometry)
                scene.query.desired[1] = side * 53.2
                for _ in range(120):
                    position = scene.frame()
                    self.assertGreaterEqual(40 - side * position[1], 11.9 - 1e-8)
                if band < .05:
                    self.assertGreater(side * position[1], 27.9)
                self.assertEqual(scene.resolver.diagnostics.errors, 0)

    def test_unknown_overlap_must_be_cleared_before_recovery_after_wall_moves(self):
        geometry = UnknownOverlapGeometry(planes=(((1, 0, 0), -253), ((0, -1, 0), -40)))
        scene = Scene(geometry)
        self.assertEqual(scene.frame()[1], 0)
        geometry.planes = (((0, -1, 0), -40),)
        first = scene.frame()[1]
        self.assertGreater(first, 0)
        self.assertLess(first, 28)
        for _ in range(120):
            position = scene.frame()
            self.assertGreaterEqual(40 - position[1], 12 - 1e-8)
        self.assertAlmostEqual(position[1], 28)
        self.assertEqual(scene.resolver.diagnostics.errors, 0)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
