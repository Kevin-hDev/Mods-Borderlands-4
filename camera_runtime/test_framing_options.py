"""Read SDK-backed choices; the menu transaction remains the only persistence authority."""
import sys
import unittest
from types import SimpleNamespace as NS


class Option:
    def __init__(self, identifier, value, *args, **kwargs):
        self.identifier, self.value = identifier, value


sys.modules["mods_base"] = NS(SliderOption=Option, BoolOption=Option)
from apex_camera_runtime.framing_options import FramingOptions


class OptionsTests(unittest.TestCase):
    def setUp(self):
        self.notes = []
        self.options = FramingOptions(self.notes.append)

    def test_missing_fields_use_new_defaults(self):
        self.assertEqual(self.options.snapshot(), ((15, False), (10, False), (0, False)))

    def test_manual_value_equal_to_preset_stays_custom_after_reopening(self):
        self.options.options[0].value = 15
        self.options.options[1].value = True
        saved = {option.identifier: option.value for option in self.options.options}
        reopened = FramingOptions()
        for option in reopened.options:
            option.value = saved[option.identifier]
        self.assertEqual(reopened.read("zoom"), (15, True))
        reopened.options[0].value, reopened.options[1].value = 25, False
        self.assertEqual(reopened.read("zoom"), (25, False))

    def test_invalid_loaded_value_falls_back_without_mutating_the_sdk_option(self):
        for value, custom in ((True, True), (-1, True), (51, True), ("25", True),
                              (17, False), (25, 1)):
            with self.subTest(value=value, custom=custom):
                self.options.options[0].value, self.options.options[1].value = value, custom
                self.assertEqual(self.options.read("zoom"), (15, False))
                self.assertIs(self.options.options[0].value, value)
                self.assertIs(self.options.options[1].value, custom)

    def test_invalid_loaded_group_does_not_discard_other_valid_values(self):
        self.options.options[0].value = float("inf")
        self.options.options[4].value, self.options.options[5].value = 20, True
        self.assertEqual(self.options.read("zoom"), (15, False))
        self.assertEqual(self.options.read("zoom"), (15, False))
        self.assertEqual(self.options.read("height"), (20, True))
        self.assertEqual(len(self.notes), 1)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
