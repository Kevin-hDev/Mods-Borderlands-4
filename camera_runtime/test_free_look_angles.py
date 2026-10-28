"""At the wheel, the mouse turn goes to the camera alone while the view stays where it was locked."""

import unittest

from apex_camera_runtime.free_look_angles import PITCH_LIMIT, Look, turn


class LookTests(unittest.TestCase):
    def test_turn_keeps_the_same_direction_between_minus_and_plus_180(self):
        self.assertAlmostEqual(turn(350.0), -10.0)
        self.assertAlmostEqual(turn(-190.0), 170.0)
        self.assertAlmostEqual(turn(90.0), 90.0)

    def test_the_camera_follows_the_view_the_game_rebuilt_and_the_view_stays(self):
        look = Look(0.0, 100.0)
        self.assertEqual(look.absorb(0.0, 110.0), (0.0, 100.0))
        # The game's next view is the turned camera plus 5 more degrees of mouse.
        self.assertEqual(look.absorb(0.0, 100.0 + look.yaw + 5.0), (0.0, 100.0))
        self.assertAlmostEqual(look.yaw, 15.0)

    def test_turning_across_180_stays_continuous(self):
        look = Look(0.0, 175.0)
        look.absorb(0.0, -175.0)
        self.assertAlmostEqual(look.yaw, 10.0)

    def test_pitch_read_as_0_to_360_and_bounded(self):
        look = Look(350.0, 0.0)
        look.absorb(340.0, 0.0)
        self.assertAlmostEqual(look.pitch, -10.0)
        look.absorb(260.0, 0.0)
        self.assertAlmostEqual(look.anchor[0] + look.pitch, -PITCH_LIMIT)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
