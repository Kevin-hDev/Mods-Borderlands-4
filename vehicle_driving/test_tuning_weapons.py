"""Weapon damage: the guns' damage formula is the game's own, raised while driving and put back, whatever happens to
the vehicle, never multiplied twice, found once the driver sits, and left to the game when the game refuses it."""
import importlib
import sys
import unittest

import sdk_stubs
from tuning_fixture import FACTORS

state = sdk_stubs.install()
from vehicle_driving import damage_formula, tuning  # noqa: E402


class Tests(unittest.TestCase):
    def setUp(self):
        # A new game: the formula module forgets the game's value and any refusal.
        importlib.reload(damage_formula)
        self.library = state["formula"]
        self.library.typed, self.library.resolves = True, True
        self.scalar = self.library.definition.Value.Scalar
        self.scalar.constant = 1.0
        self.driver = sdk_stubs.Driver()
        self.owner = tuning.Tuning()

    def test_raised_while_driving_and_put_back_after_the_vehicle_is_destroyed(self):
        car = sdk_stubs.Vehicle('OakVehicle_7', self.driver)
        self.owner.take(car)
        self.owner.update(FACTORS)
        self.assertEqual(self.scalar.constant, 3.0)
        sdk_stubs.destroy(car)
        self.assertEqual(self.owner.put_back(), [])
        self.assertEqual(self.scalar.constant, 1.0)

    def test_a_raise_left_behind_is_never_multiplied_again(self):
        car = sdk_stubs.Vehicle('OakVehicle_8', self.driver)
        self.owner.take(car)
        self.owner.update(FACTORS)
        # The mod's frame stopped before any put back: the formula is still raised when the next vehicle comes.
        self.owner = tuning.Tuning()
        self.owner.take(sdk_stubs.Vehicle('OakVehicle_9', self.driver))
        lines = self.owner.update(FACTORS)
        self.assertEqual(self.scalar.constant, 3.0)
        self.assertIn('calc_vehicle_weapon_damage.Scalar 1.000->3.000', lines[0])
        self.owner.put_back()
        self.assertEqual(self.scalar.constant, 1.0)

    def test_found_once_the_driver_sits_and_put_back(self):
        car = sdk_stubs.Vehicle('OakVehicle_10', self.driver)
        car.DriverPawn = None
        lines = self.owner.take(car)
        self.assertIn('calc_vehicle_weapon_damage not found on OakVehicle_10: left to the game', lines)
        self.owner.update(FACTORS)
        self.assertEqual(self.scalar.constant, 1.0)
        car.DriverPawn = self.driver
        lines = self.owner.update(FACTORS)
        self.assertEqual(self.scalar.constant, 3.0)
        self.assertTrue(any('calc_vehicle_weapon_damage' in line and 'found on OakVehicle_10' in line
                            for line in lines))
        self.owner.put_back()
        self.assertEqual(self.scalar.constant, 1.0)

    def test_a_formula_the_game_refuses_is_left_to_it_and_the_rest_written(self):
        self.library.resolves = False
        car = sdk_stubs.Vehicle('OakVehicle_11', self.driver)
        self.owner.take(car)
        self.owner.update(FACTORS)
        self.assertEqual(self.scalar.constant, 1.0)
        self.assertEqual(car.OakVehicleMovement.HoverSetup.PowerslideJumpHeight.constant, 330.0)
        calls = len(self.library.calls)
        self.owner.update(FACTORS)
        self.assertEqual(len(self.library.calls), calls)
        self.owner.put_back()

    def test_a_lever_that_never_comes_never_asks_the_formula_again(self):
        # Another model of vehicle, whose driver never has the boost's cost: looked for again at every check.
        del self.driver.VehicleDriverComponent.VehicleAttributesState.BoostConsumptionRateScalar
        self.owner.take(sdk_stubs.Vehicle('OakVehicle_12', self.driver))
        asked = len(self.library.calls)
        for _ in range(5):
            self.owner.update(FACTORS)
        self.assertEqual(len(self.library.calls), asked)
        self.assertEqual(self.scalar.constant, 3.0)
        self.owner.update(dict(FACTORS, weapon_damage=2.0))
        self.assertEqual(self.scalar.constant, 2.0)
        self.owner.put_back()
        self.assertEqual(self.scalar.constant, 1.0)

    def test_a_formula_the_game_refused_is_not_waited_for(self):
        self.library.resolves = False
        self.owner.take(sdk_stubs.Vehicle('OakVehicle_13', self.driver))
        self.assertEqual(self.owner._waiting, set())
        self.owner.put_back()


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    sys.exit(not result.wasSuccessful())
