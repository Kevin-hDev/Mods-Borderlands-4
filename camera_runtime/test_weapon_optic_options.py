"""The optic rows are one saved number each: 0 is "BDL4", a bit per zoom of the row; "BDL4" and a zoom are never
ticked together, a hand-edited value reads as "BDL4", and a new install keeps the aim each weapon had before its row:
x1 for pistols, SMGs, shotguns and assault rifles, "BDL4" for sniper rifles and heavy weapons."""

import sys
import unittest
from types import SimpleNamespace as NS


class Option:
    def __init__(self, identifier, value, min_value=None, max_value=None, *args, **kwargs):
        self.identifier, self.value, self.kwargs = identifier, value, kwargs
        self.min_value, self.max_value = min_value, max_value


sys.modules["mods_base"] = NS(SliderOption=Option, BoolOption=Option)

from apex_camera_runtime.weapon_optic_options import (CHOICES_OF, IDENTIFIERS, WeaponOpticOptions,  # noqa: E402
                                                      ticked, toggled)

COMMANDS = NS(option=lambda identifier: NS(value={"sniper_zoom_key": "A",
                                                  "sniper_zoom_controller": "Gamepad_LeftThumbstick"}[identifier]))
SNIPER = CHOICES_OF["sniper_optics"]
PISTOL = CHOICES_OF["pistol_optics"]


class OptionTests(unittest.TestCase):
    def test_one_row_per_weapon_type_in_the_games_order_with_kevins_zooms(self):
        self.assertEqual(IDENTIFIERS, ("pistol_optics", "smg_optics", "shotgun_optics", "assault_optics",
                                       "sniper_optics", "heavy_optics"))
        self.assertEqual([CHOICES_OF[name] for name in IDENTIFIERS],
                         [(1, 2, 3), (1, 2, 3, 4), (1, 2), (1, 2, 3, 4), (2, 3, 4, 6, 8), (1, 2)])

    def test_a_new_install_keeps_the_aim_each_weapon_had(self):
        options = WeaponOpticOptions(COMMANDS)
        self.assertEqual([option.identifier for option in options.options], list(IDENTIFIERS))
        self.assertEqual([options.weapon_ticked(category) for category in range(1, 7)],
                         [(1,), (1,), (1,), (1,), (), ()])
        self.assertEqual(options.sniper_ticked(), ())
        for option in options.options:
            self.assertIs(option.kwargs["is_hidden"], True)
            self.assertEqual(option.min_value, 0)
            self.assertEqual(option.max_value, (1 << len(CHOICES_OF[option.identifier])) - 1)

    def test_a_weapon_type_without_a_row_is_bdl4(self):
        options = WeaponOpticOptions(COMMANDS)
        for category in (None, 0, 7, 8, "1"):
            with self.subTest(category=category):
                self.assertEqual(options.weapon_ticked(category), ())

    def test_each_row_reads_its_own_value(self):
        options = WeaponOpticOptions(COMMANDS)
        options.options[0].value = 0b110
        options.options[4].value = 0b10100
        self.assertEqual(options.weapon_ticked(1), (2, 3))
        self.assertEqual(options.sniper_ticked(), (4, 8))

    def test_the_zoom_keys_come_from_the_commands_page(self):
        self.assertEqual(WeaponOpticOptions(COMMANDS).keys(), ("A", "Gamepad_LeftThumbstick"))

    def test_each_bit_is_a_zoom_of_the_row_smallest_first(self):
        self.assertEqual(ticked(0b00001, SNIPER), (2,))
        self.assertEqual(ticked(0b10100, SNIPER), (4, 8))
        self.assertEqual(ticked(0b11111, SNIPER), (2, 3, 4, 6, 8))
        self.assertEqual(ticked(5.0, SNIPER), (2, 4))
        self.assertEqual(ticked(0b101, PISTOL), (1, 3))

    def test_a_hand_edited_value_reads_as_bdl4(self):
        for value in (-1, 0b1000, 2.5, "3", True, None, float("nan")):
            with self.subTest(value=value):
                self.assertEqual(ticked(value, PISTOL), ())

    def test_ticking_a_zoom_unticks_bdl4_and_unticking_the_last_ticks_it_again(self):
        mask = toggled(0, 6, SNIPER)
        self.assertEqual(ticked(mask, SNIPER), (6,))
        mask = toggled(mask, 3, SNIPER)
        self.assertEqual(ticked(mask, SNIPER), (3, 6))
        mask = toggled(toggled(mask, 3, SNIPER), 6, SNIPER)
        self.assertEqual(mask, 0)
        self.assertEqual(ticked(toggled(toggled(1, 1, PISTOL), 3, PISTOL), PISTOL), (3,))

    def test_the_bdl4_box_unticks_every_zoom(self):
        self.assertEqual(toggled(0b11111, None, SNIPER), 0)
        self.assertEqual(toggled(0, None, PISTOL), 0)

    def test_a_click_on_a_hand_edited_value_starts_from_bdl4(self):
        self.assertEqual(ticked(toggled(99, 2, SNIPER), SNIPER), (2,))


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(OptionTests))
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
