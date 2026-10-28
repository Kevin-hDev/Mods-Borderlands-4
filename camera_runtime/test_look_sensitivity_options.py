"""Look and aim in percent of the game's sensitivity, 100 by default; a hand-edited value reads as 100. The weapon
types count only while their switch is on, and the sniper rifle's optic zooms only while theirs is on too."""

import sys
import unittest
from types import SimpleNamespace as NS


class Option:
    def __init__(self, identifier, value, min_value=None, max_value=None, *args, **kwargs):
        self.identifier, self.value, self.kwargs = identifier, value, kwargs
        self.min_value, self.max_value = min_value, max_value


sys.modules["mods_base"] = NS(SliderOption=Option, BoolOption=Option)

from apex_camera_runtime.look_sensitivity_options import (  # noqa: E402
    PAGE, PER_OPTIC, WEAPON_PREFIX, LookSensitivityOptions)


class OptionTests(unittest.TestCase):
    def test_percent_of_the_game_and_bounds(self):
        options = LookSensitivityOptions()
        self.assertEqual(tuple(option.identifier for option in options.options), PAGE)
        self.assertEqual(options.values(), (1.0, 1.0, {}))
        self.assertEqual((options.look.min_value, options.look.max_value), (25, 200))
        options.look.value, options.aim.value = 80, 150
        self.assertEqual(options.values(), (0.8, 1.5, {}))
        options.look.value, options.aim.value = 900, 5
        self.assertEqual(options.values(), (2.0, 0.25, {}))
        options.look.value, options.aim.value = "80", True
        self.assertEqual(options.values(), (1.0, 1.0, {}))

    def test_weapon_types_count_only_while_switched_on(self):
        options = LookSensitivityOptions()
        self.assertIs(options.per_weapon.value, False)
        self.assertEqual([option.identifier for option in options.weapons],
                         [WEAPON_PREFIX + name for name in ("pistol", "smg", "shotgun", "assault", "sniper",
                                                            "heavy")])
        options.weapons[0].value, options.weapons[3].value, options.weapons[4].value = 150, 9000, 60
        options.weapons[5].value = 70
        self.assertEqual(options.values()[2], {})
        options.per_weapon.value = True
        self.assertEqual(options.values()[2], {"pistol": 1.5, "smg": 1.0, "shotgun": 1.0, "assault": 2.0,
                                               "sniper": 0.6, "heavy": 0.7})
        options.per_weapon.value = 1
        self.assertEqual(options.values()[2], {})

    def test_one_sniper_value_unless_its_optic_zooms_are_switched_on(self):
        """Kevin, 2026-10-09: one sniper rifle value, the rows per zoom folded under a switch off by default."""
        options = LookSensitivityOptions()
        self.assertEqual(options.per_optic.identifier, PER_OPTIC)
        self.assertTrue(PER_OPTIC.startswith(WEAPON_PREFIX))
        self.assertIs(options.per_optic.value, False)
        self.assertEqual([option.identifier for option in options.optics],
                         [f"{WEAPON_PREFIX}sniper_x{zoom}" for zoom in (2, 3, 4, 6, 8)])
        options.weapons[4].value, options.optics[0].value, options.optics[4].value = 80, 150, 40
        options.per_optic.value = True
        # The two switches are independent (Kevin, 2026-10-10: « ce sont deux réglages indépendants »).
        self.assertEqual(options.values()[2], {"sniper_x2": 1.5, "sniper_x3": 1.0, "sniper_x4": 1.0,
                                               "sniper_x6": 1.0, "sniper_x8": 0.4})
        options.per_weapon.value = True
        self.assertEqual(options.values()[2], {"pistol": 1.0, "smg": 1.0, "shotgun": 1.0, "assault": 1.0,
                                               "sniper": 0.8, "heavy": 1.0, "sniper_x2": 1.5, "sniper_x3": 1.0,
                                               "sniper_x4": 1.0, "sniper_x6": 1.0, "sniper_x8": 0.4})
        options.per_optic.value = "on"
        self.assertEqual(options.values()[2], {"pistol": 1.0, "smg": 1.0, "shotgun": 1.0, "assault": 1.0,
                                               "sniper": 0.8, "heavy": 1.0})


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
