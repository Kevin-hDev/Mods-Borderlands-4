"""A camera sweep protects volume and uses both simple and detailed geometry."""
from types import SimpleNamespace as NS
import importlib.util
import unittest


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

    def test_unknown_zero_depth_overlap_is_not_a_clear_endpoint(self):
        overlap = NS(Distance=0, PenetrationDepth=0, bStartPenetrating=True)
        self.answers = [(True, overlap), (True, overlap)]
        self.assertFalse(self.trace.endpoint_clear(self.actor, (0, 0, 0)))
        self.assertEqual(len(self.calls), 2)

    def test_endpoint_contact_requires_a_real_clear_smaller_probe(self):
        contact = NS(Distance=0, PenetrationDepth=0, bStartPenetrating=True)
        self.answers = [(True, contact), (False, NS()), (False, NS())]
        self.assertTrue(self.trace.endpoint_clear(self.actor, (0, 0, 0)))
        self.assertEqual([call[5] for call in self.calls], [False, False, True])
        self.assertGreaterEqual(self.calls[1][3], 11.9)
        self.assertLess(self.calls[1][3], 12)
        for call in self.calls:
            self.assertLess(call[1].X, 0)
            self.assertGreater(call[2].X, 0)
            self.assertAlmostEqual((call[1].X + call[2].X) / 2, 0)
            self.assertLessEqual(call[2].X - call[1].X, .02)
            self.assertEqual((call[1].Y, call[1].Z, call[2].Y, call[2].Z), (0, 0, 0, 0))

    def test_detailed_overlap_remains_blocked_after_simple_geometry_is_clear(self):
        overlap = NS(Distance=0, PenetrationDepth=0, bStartPenetrating=True)
        self.answers = [(False, NS()), (True, overlap), (True, overlap)]
        self.assertFalse(self.trace.endpoint_clear(self.actor, (0, 0, 0)))
        self.assertEqual([call[5] for call in self.calls], [False, True, True])

    def test_stationary_proof_failure_is_not_a_clear_contact(self):
        self.answers = [(True, NS(Distance=0, PenetrationDepth=0)), OSError('trace unavailable')]
        with self.assertRaises(OSError):
            self.trace.endpoint_clear(self.actor, (0, 0, 0))

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

    def test_release_contact_proof_also_keeps_the_total_one_mm_budget(self):
        contact = NS(Distance=0, PenetrationDepth=0, bStartPenetrating=True)
        self.answers = [(True, contact), (False, NS()), (True, contact), (False, NS())]
        self.assertTrue(self.trace.endpoint_clear(self.actor, (0, 0, 0), extra_margin=1))
        self.assertEqual(len(self.calls), 4)
        self.assertGreaterEqual(min(call[3] for call in self.calls), 12.9 - 1e-9)
        self.assertLessEqual(max(call[3] for call in self.calls), 13)

    def test_near_future_hit_is_not_a_departure_overlap_even_with_stale_depth(self):
        self.answers = [(True, NS(Distance=.03, PenetrationDepth=2, bStartPenetrating=False)),
                        (False, NS()), (False, NS())]
        self.assertEqual(self.trace.distance(self.actor, (0, 0, 0), (100, 0, 0)), 0)
        self.assertEqual(len(self.calls), 2)
        self.assertFalse(self.trace.reduced)

    def test_future_contact_beyond_one_mm_keeps_its_positive_distance(self):
        self.answers = [(True, NS(Distance=.15, bStartPenetrating=False)), (False, NS())]
        self.assertEqual(self.trace.distance(self.actor, (0, 0, 0), (100, 0, 0)), .15)
        self.assertFalse(self.trace.reduced)

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


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
