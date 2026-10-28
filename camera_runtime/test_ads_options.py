"""The saved aiming choice defaults to shoulder view and rolls back failed saves."""

import importlib.util
import sys
import unittest
from types import SimpleNamespace as NS


class Option:
    def __init__(self, identifier, value, **kwargs):
        self.identifier, self.value, self.default_value = identifier, value, value
        self.__dict__.update(kwargs)


sys.modules["mods_base"] = NS(BoolOption=Option)


class AdsOptionsTests(unittest.TestCase):
    def make_options(self):
        self.assertIsNotNone(importlib.util.find_spec("apex_camera_runtime.ads_options"),
                             "shared ADS choice missing")
        from apex_camera_runtime.ads_options import AdsOptions
        options = AdsOptions()
        options.option.mod = NS(save_settings=lambda: None)
        return options

    def test_default_and_existing_first_person_choice(self):
        options = self.make_options()
        self.assertEqual(options.option.identifier, "third_person_ads")
        self.assertIs(options.option.default_value, True)
        self.assertTrue(options.enabled())
        options.option.value = False
        self.assertFalse(options.enabled())
        self.assertEqual(options.option.true_text, "Third Person")
        self.assertEqual(options.option.false_text, "First Person")

    def test_invalid_choice_never_enables_aim_presentation(self):
        options = self.make_options()
        for value in (None, 1, 0, "True", [], {}):
            options.option.value = value
            self.assertFalse(options.enabled())
            with self.assertRaises(ValueError):
                options.save(value)

    def test_save_failure_restores_previous_choice(self):
        options = self.make_options()
        options.save(False)
        def fail():
            raise OSError("save unavailable")
        options.option.mod.save_settings = fail
        with self.assertRaises(OSError):
            options.save(True)
        self.assertFalse(options.enabled())


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
