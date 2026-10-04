"""Weapon damage follows late loading and never writes destroyed behaviors."""
import sys
import unittest

import sdk_stubs
from tuning_fixture import FACTORS

sdk_stubs.install()
from vehicle_driving import tuning  # noqa: E402


class Tests(unittest.TestCase):
    def setUp(self):
        self.driver = sdk_stubs.Driver()
        self.attributes = self.driver.VehicleDriverComponent.VehicleAttributesState
        self.owner = tuning.Tuning()

    def test_destroyed_behavior_is_never_written_again(self):
        car = sdk_stubs.Vehicle('OakVehicle_7', self.driver)
        self.owner.take(car)
        self.owner.update(FACTORS)
        gone = car.VehicleWeapons[0].behaviors[0]
        sdk_stubs.destroy(gone)
        gone.damage.Value = 999.0
        self.assertEqual(self.owner.update(FACTORS), [])
        self.assertEqual(gone.damage.Value, 999.0)
        self.owner.put_back()
        self.assertEqual(gone.damage.Value, 999.0)
        self.assertEqual(car.VehicleWeapons[1].behaviors[0].damage.Value, 2.8)
        self.assertEqual(self.attributes.MaxAccel.BaseValue, 1000.0)

    def test_missing_weapons_are_found_later_and_restored(self):
        car = sdk_stubs.Vehicle('OakVehicle_8', self.driver)
        arsenal = car.VehicleWeapons
        car.VehicleWeapons = []
        self.assertEqual(self.owner.take(car), [
            'driving OakVehicle_8', 'VehicleWeapons not found on OakVehicle_8: left to the game'])
        self.owner.update(FACTORS)
        car.VehicleWeapons = arsenal
        lines = self.owner.update(FACTORS)
        self.assertAlmostEqual(arsenal[0].behaviors[0].damage.Value, 8.4)
        self.assertTrue(any('VehicleWeapons found on OakVehicle_8' in line for line in lines))
        self.assertEqual(car.OakVehicleMovement.HoverSetup.PowerslideJumpHeight.constant, 330.0)
        self.owner.put_back()
        self.assertEqual(arsenal[0].behaviors[0].damage.Value, 2.8)

    def test_first_vehicle_delayed_firing_behaviors_are_found_and_restored(self):
        # Session 13: weapons existed at summon, but their firing behaviors arrived later.
        car = sdk_stubs.Vehicle('OakVehicle_9', self.driver)
        firing = [weapon.behaviors for weapon in car.VehicleWeapons]
        for weapon in car.VehicleWeapons:
            weapon.behaviors = []
        lines = self.owner.take(car)
        self.assertEqual(lines[1:], [
            f'weapon[{index}].damage not found on OakVehicle_9: left to the game'
            for index in range(4)])
        self.owner.update(FACTORS)
        for weapon, behaviors in zip(car.VehicleWeapons, firing):
            weapon.behaviors = behaviors
        lines = self.owner.update(FACTORS)
        for index, behaviors in enumerate(firing):
            self.assertAlmostEqual(behaviors[0].damage.Value, 8.4 if index < 2 else 21.0)
        message = 'weapon[0].damage, weapon[1].damage, weapon[2].damage, weapon[3].damage found on OakVehicle_9'
        self.assertTrue(any(message in line for line in lines))
        self.owner.put_back()
        self.assertEqual([behaviors[0].damage.Value for behaviors in firing], [2.8, 2.8, 7.0, 7.0])


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    sys.exit(not result.wasSuccessful())
