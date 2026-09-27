"""The wanted foot mode and the native suspension change as one authority."""

import unittest

from apex_camera_runtime.constants import ORBIT_MODE, THIRD_PERSON_MODE
from apex_camera_runtime.third_person import ThirdPersonController
from camera_test_fixtures import Bridge, Hooks


class DesiredModeTests(unittest.TestCase):
    def test_mode_and_orbit_suspension_never_diverge(self):
        controller = ThirdPersonController(Hooks(), Bridge(), "desired_mode")
        controller.set_desired_mode(ORBIT_MODE)
        self.assertEqual(controller._desired_mode, ORBIT_MODE)
        self.assertIn("orbit", controller._suspensions)
        controller.set_desired_mode(THIRD_PERSON_MODE)
        self.assertEqual(controller._desired_mode, THIRD_PERSON_MODE)
        self.assertNotIn("orbit", controller._suspensions)

    def test_unknown_mode_is_rejected_without_mutation(self):
        controller = ThirdPersonController(Hooks(), Bridge(), "desired_mode_invalid")
        with self.assertRaises(ValueError):
            controller.set_desired_mode("Default")
        self.assertEqual(controller._desired_mode, THIRD_PERSON_MODE)
        self.assertNotIn("orbit", controller._suspensions)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
