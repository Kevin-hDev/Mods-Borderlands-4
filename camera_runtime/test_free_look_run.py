"""Free Look's run: kept only when moving, at the speed pushed at the press, turned by left and right."""

import unittest

from apex_camera_runtime.free_look_run import DEAD_ZONE, TURN_DEG_S, braking, lateral, start


class RunTests(unittest.TestCase):
    def test_standing_still_keeps_no_run(self):
        self.assertIsNone(start(10.0, 1.0, 90.0))

    def test_the_speed_pushed_at_the_press_is_kept(self):
        self.assertEqual(start(600.0, 0.5, 0.0).scale, 0.5)
        self.assertEqual(start(600.0, 1.0, 0.0).scale, 1.0)

    def test_no_push_while_moving_counts_as_full(self):
        self.assertEqual(start(900.0, 0.0, 0.0).scale, 1.0)

    def test_right_turns_the_run_right_and_left_turns_it_left(self):
        run = start(600.0, 1.0, 0.0)
        self.assertAlmostEqual(run.steer(1.0, 0.5), TURN_DEG_S * 0.5)
        self.assertAlmostEqual(run.steer(-1.0, 1.0), -TURN_DEG_S * 0.5)

    def test_a_small_push_does_not_turn(self):
        run = start(600.0, 1.0, 30.0)
        self.assertAlmostEqual(run.steer(DEAD_ZONE / 2, 1.0), 30.0)

    def test_the_run_turns_past_the_back(self):
        run = start(600.0, 1.0, 170.0)
        self.assertAlmostEqual(run.steer(1.0, 20.0 / TURN_DEG_S), -170.0)

    def test_forward_points_along_the_run(self):
        x, y = start(600.0, 1.0, 90.0).forward()
        self.assertAlmostEqual(x, 0.0)
        self.assertAlmostEqual(y, 1.0)

    def test_keys_and_stick_add_and_stay_within_one(self):
        self.assertEqual(lateral(1.0, 0.0, 0.0), 1.0)
        self.assertEqual(lateral(0.0, 1.0, 0.0), -1.0)
        self.assertEqual(lateral(1.0, 0.0, 1.0), 1.0)
        self.assertAlmostEqual(lateral(0.0, 0.0, -0.4), -0.4)

    def test_braking_needs_a_real_push(self):
        self.assertFalse(braking(0.0, 0.1))
        self.assertTrue(braking(1.0, 0.0))
        self.assertTrue(braking(0.0, 0.8))


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
