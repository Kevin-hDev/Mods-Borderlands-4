"""Free Look's options: a switch, on by default, then hold or press for each device and the hold time; switched off,
there are no values, so the keys do nothing (Kevin, 2026-10-08)."""

import sys
import unittest
from types import SimpleNamespace as NS


class Option:
    def __init__(self, identifier, value, min_value=None, max_value=None, *args, **kwargs):
        self.identifier, self.value, self.kwargs = identifier, value, kwargs
        self.min_value, self.max_value = min_value, max_value


sys.modules["mods_base"] = NS(SliderOption=Option, BoolOption=Option)

from apex_camera_runtime.free_look_options import (CONTROLLER_ID, DEFAULT_HOLD_S, KEYBOARD_ID,  # noqa: E402
                                                   FreeLookOptions)


class Commands:
    def __init__(self):
        self.keys = {KEYBOARD_ID: Option(KEYBOARD_ID, "A"), CONTROLLER_ID: Option(CONTROLLER_ID, "Gamepad_LeftThumbstick")}

    def option(self, identifier):
        return self.keys[identifier]


class OptionTests(unittest.TestCase):
    def test_the_switch_comes_first_and_is_on(self):
        options = FreeLookOptions(Commands())
        self.assertEqual([option.identifier for option in options.options],
                         ["free_look", "free_look_keyboard_hold", "free_look_controller_hold", "free_look_hold_time"])
        self.assertIs(options.switch.value, True)
        self.assertEqual(options.switch.kwargs["display_name"], "Free Look")

    def test_on_it_gives_the_keys_and_holds(self):
        values = FreeLookOptions(Commands()).values()
        self.assertEqual((values.keys, values.holds, values.hold_s),
                         (("A", "Gamepad_LeftThumbstick"), (True, True), DEFAULT_HOLD_S))

    def test_off_it_gives_nothing(self):
        options = FreeLookOptions(Commands())
        options.switch.value = False
        self.assertIsNone(options.values())

    def test_a_hand_edited_switch_stays_on(self):
        options = FreeLookOptions(Commands())
        options.switch.value = "no"
        self.assertIsNotNone(options.values())


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
