"""A camera sweep protects volume and uses both simple and detailed geometry."""
from types import SimpleNamespace as NS
import importlib.util
import unittest

from collision_geometry_fixtures import Geometry


class Tests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("apex_camera_runtime.collision_sweep"),
                             "Volume-based camera sweep is missing")
        from apex_camera_runtime.collision_sweep import SphereSweep
        self.calls = []
        self.answers = []
        self.actor = object()
        self.sdk = NS(make_struct=lambda name, **kw: NS(kind=name, **kw))
        self.trace = SphereSweep(NS(SphereTraceSingle=self.call), self.sdk)

    def call(self, *args):
        self.calls.append(args)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    def test_volume_simple_and_complex_return_the_nearest_safe_distance(self):
        self.answers = [(False, [], NS()), (True, [], NS(Distance=24, bStartPenetrating=False))]
        distance = self.trace.distance(self.actor, (0, 0, 0), (100, 0, 0))
        self.assertEqual(distance, 24)
        self.assertEqual(len(self.calls), 2)
        for call, complex_trace in zip(self.calls, (False, True)):
            self.assertGreater(call[3], 0)
            self.assertEqual(call[5], complex_trace)
            self.assertEqual(call[6], [self.actor])
            self.assertIs(call[0], self.actor)

    def test_nearby_wall_limits_the_sphere_center_without_subtracting_radius_twice(self):
        self.answers = [(True, [], NS(Distance=18)), (True, [], NS(Distance=28))]
        self.assertEqual(self.trace.distance(self.actor, (0, 0, 0), (100, 0, 0)), 18)

    def test_nearest_contact_is_kept_for_the_automatic_shoulder_log(self):
        nearer = NS(Distance=18)
        self.answers = [(True, [], nearer), (True, [], NS(Distance=28))]
        self.trace.distance(self.actor, (0, 0, 0), (100, 0, 0))
        self.assertIs(self.trace.hit, nearer)
        self.answers = [(False, [], NS()), (False, [], NS())]
        self.trace.distance(self.actor, (0, 0, 0), (100, 0, 0))
        self.assertIsNone(self.trace.hit)

    def test_clear_path_preserves_the_exact_requested_position(self):
        self.answers = [(False, [], NS()), (False, [], NS())]
        self.assertEqual(self.trace.distance(self.actor, (0, 0, 0), (0, 30, 40)), 50)

    def test_invalid_hit_and_initial_penetration_refuse_custom_placement(self):
        for hit in (NS(Distance=float("nan")), NS(Distance=-1), NS(Distance=101),
                    NS(Distance=0, bStartPenetrating=True)):
            self.answers = [(True, [], hit)]
            with self.assertRaises(ValueError):
                self.trace.distance(self.actor, (0, 0, 0), (100, 0, 0))

    def test_trace_failure_propagates_instead_of_claiming_clearance(self):
        self.answers = [OSError("trace unavailable")]
        with self.assertRaises(OSError):
            self.trace.distance(self.actor, (0, 0, 0), (100, 0, 0))

    def test_native_camera_eight_units_from_wall_rechecks_its_available_volume(self):
        self.answers = [(True, [], NS(Distance=0, bStartPenetrating=True, PenetrationDepth=4)),
                        (False, [], NS()), (False, [], NS())]
        self.assertEqual(self.trace.distance(self.actor, (0, 0, 0), (0, 40, 0)), 40)
        self.assertEqual([call[3] for call in self.calls][::2], [12, 12])
        self.assertGreaterEqual(self.calls[1][3], 7.9)
        self.assertLess(self.calls[1][3], 8)

    def test_reduced_volume_still_checks_a_second_obstacle(self):
        self.answers = [(True, [], NS(Distance=0, bStartPenetrating=True, PenetrationDepth=2)),
                        (True, [], NS(Distance=12)), (False, [], NS())]
        self.assertEqual(self.trace.distance(self.actor, (0, 0, 0), (0, 40, 0)), 12)

    def test_two_rechecks_recover_rounded_contact_without_exceeding_one_mm(self):
        def rounded(*args):
            self.calls.append(args)
            return args[3] > 11.925, NS(Distance=0, PenetrationDepth=0, bStartPenetrating=True)
        self.trace.kismet.SphereTraceSingle = rounded
        self.assertEqual(self.trace.distance(self.actor, (0, 0, 0), (100, 0, 0)), 100)
        self.assertEqual(len(self.calls), 6)
        self.assertGreaterEqual(min(call[3] for call in self.calls), 11.9 - 1e-9)
        self.assertLessEqual(max(call[3] for call in self.calls), 12)
        for call in self.calls:
            self.assertEqual((call[1].X, call[2].X), (0, 100))

    def test_persistent_rounded_contact_stops_at_total_one_mm_budget(self):
        def overlap(*args):
            self.calls.append(args)
            return True, NS(Distance=0, PenetrationDepth=0, bStartPenetrating=True)
        self.trace.kismet.SphereTraceSingle = overlap
        self.assertEqual(self.trace.distance(self.actor, (0, 0, 0), (100, 0, 0)), 0)
        self.assertEqual(len(self.calls), 6)
        self.assertGreaterEqual(min(call[3] for call in self.calls), 11.9 - 1e-9)

    def test_near_future_hit_is_not_a_departure_overlap_even_with_stale_depth(self):
        self.answers = [(True, NS(Distance=.03, PenetrationDepth=2, bStartPenetrating=False)),
                        (False, NS()), (False, NS())]
        self.assertEqual(self.trace.distance(self.actor, (0, 0, 0), (100, 0, 0)), 0)
        self.assertEqual(len(self.calls), 2)

    def test_future_contact_beyond_one_mm_keeps_its_positive_distance(self):
        self.answers = [(True, NS(Distance=.15, bStartPenetrating=False)), (False, NS())]
        self.assertEqual(self.trace.distance(self.actor, (0, 0, 0), (100, 0, 0)), .15)

    def test_initial_depth_larger_than_sphere_is_rejected_not_silently_blocked(self):
        for depth in (12.001, 13):
            self.answers = [(True, NS(Distance=0, bStartPenetrating=True, PenetrationDepth=depth)),
                            (False, NS())]
            with self.assertRaises(ValueError):
                self.trace.distance(self.actor, (0, 0, 0), (100, 0, 0))

    def test_zero_distance_nonpenetrating_hit_cannot_spend_a_stale_depth(self):
        def contact(*args):
            self.calls.append(args)
            return args[3] > 11.925, NS(Distance=0, PenetrationDepth=2, bStartPenetrating=False)
        self.trace.kismet.SphereTraceSingle = contact
        self.assertEqual(self.trace.distance(self.actor, (0, 0, 0), (100, 0, 0)), 100)
        self.assertGreaterEqual(min(call[3] for call in self.calls), 11.9 - 1e-9)

    def test_two_rechecks_negotiate_distinct_departure_surfaces_and_later_obstacle(self):
        from apex_camera_runtime.collision_sweep import SphereSweep
        geometry = Geometry(planes=(((1, 0, 0), -258), ((0, 1, 0), -5), ((0, -1, 0), -40)))
        distance = SphereSweep(geometry, self.sdk).distance(object(), (-250, 0, 80), (-250, 53.2, 80))
        self.assertGreater(distance, 34)
        # The narrowest departure surface is at 5 cm; contact separation may spend at most 1 mm.
        self.assertLessEqual(distance, 35.1 + 1e-8)
        self.assertEqual(geometry.spheres, 6)

    def test_repeated_zero_depth_never_certifies_a_whole_segment_as_safe(self):
        from apex_camera_runtime.collision_sweep import SphereSweep
        unknown = NS(SphereTraceSingle=lambda *args: (True, NS(Distance=0, bStartPenetrating=True,
                                                               PenetrationDepth=0)))
        self.assertEqual(SphereSweep(unknown, self.sdk).distance(object(), (0, 0, 0), (0, 40, 0)), 0)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
