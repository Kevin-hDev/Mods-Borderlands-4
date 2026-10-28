"""The signal between the camera mods and Vehicle Driving at the wheel: one slot for every copy, nothing kept past a
frame long gone."""

import sys
import unittest

from apex_camera_runtime import vehicle_share


class VehicleShareTests(unittest.TestCase):
    def setUp(self):
        sys.modules.pop(vehicle_share.SLOT, None)

    def test_nothing_published_means_nothing_to_add_and_nobody_writing(self):
        self.assertEqual(vehicle_share.framing(), vehicle_share.ZERO)
        self.assertFalse(vehicle_share.claimed())

    def test_a_fresh_framing_and_claim_are_read_back(self):
        vehicle_share.publish((-80.0, 0.0, 0.0))
        vehicle_share.claim()
        self.assertEqual(vehicle_share.framing(), (-80.0, 0.0, 0.0))
        self.assertTrue(vehicle_share.claimed())

    def test_old_values_are_ignored(self):
        vehicle_share.publish((-80.0, 0.0, 0.0))
        vehicle_share.claim()
        slot = sys.modules[vehicle_share.SLOT]
        slot.framing_ns = slot.driver_ns = 1
        self.assertEqual(vehicle_share.framing(), vehicle_share.ZERO)
        self.assertFalse(vehicle_share.claimed())


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
