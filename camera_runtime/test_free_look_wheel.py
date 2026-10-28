"""Free Look at the wheel against a fake game: the view kept and the turn given to the camera, the throttle kept until
the brake, and at the release the view and the camera both back on the kept direction."""

import unittest

from free_look_test_fixtures import Controller, Sdk
from apex_camera_runtime.free_look_wheel import Wheel


def wheel(throttle=1.0, speed=1500.0):
    said = []
    pc = Controller(speed=speed, vehicle_throttle=throttle)
    unit = Wheel(Sdk(), said.append)
    unit.begin(pc)
    return unit, pc, said


class WheelTests(unittest.TestCase):
    def test_the_view_stays_and_the_camera_takes_the_turn(self):
        unit, pc, _said = wheel()
        pc.view.Yaw = 40.0
        unit.frame(pc, pc.value)
        self.assertEqual(pc.view.Yaw, 0.0)
        self.assertAlmostEqual(pc.PlayerCameraManager.CameraModeState.BaseRotationOffset.Yaw, 40.0)

    def test_the_throttle_is_kept_until_the_brake(self):
        unit, pc, _said = wheel()
        unit.frame(pc, pc.value)
        pc.held["S"] = 1.0
        unit.frame(pc, pc.value)
        unit.frame(pc, pc.value)
        self.assertEqual(pc.Pawn.OakVehicleMovement.kept, [1.0])

    def test_a_still_vehicle_keeps_no_throttle(self):
        unit, pc, _said = wheel(speed=0.0)
        unit.frame(pc, pc.value)
        self.assertEqual(pc.Pawn.OakVehicleMovement.kept, [])

    def test_the_release_puts_view_and_camera_back_and_clears_the_turn(self):
        unit, pc, _said = wheel()
        pc.view.Yaw = 90.0
        unit.frame(pc, pc.value)
        pc.view.Yaw = 88.0
        unit.release(pc)
        state = pc.PlayerCameraManager.CameraModeState
        self.assertEqual((pc.view.Yaw, state.bases, state.BaseRotationOffset.Yaw), (0.0, [0.0], 0.0))


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
