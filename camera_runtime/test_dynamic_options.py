"""Framing and motion options: on at 100 % by default; off gives 0; hand-edited values fall back to the defaults."""
import sys
import types
import unittest


class Option:
    def __init__(self, identifier, value, *args, **kwargs):
        self.identifier, self.value = identifier, value
        self.limits, self.kwargs = args, kwargs


sys.modules['mods_base'] = types.SimpleNamespace(BoolOption=Option, SliderOption=Option)
from apex_camera_runtime.dynamic_options import DynamicOptions  # noqa: E402


class OptionsTests(unittest.TestCase):
    def test_defaults(self):
        options = DynamicOptions()
        self.assertEqual(options.values(), (1.0, 1.0))
        self.assertEqual([option.identifier for option in options.options],
                         ["action_framing", "action_framing_strength", "camera_motion", "camera_motion_strength"])
        self.assertEqual(options.framing_strength.limits, (25, 200))
        self.assertEqual(options.framing_strength.kwargs["step"], 5)

    def test_switches(self):
        options = DynamicOptions()
        options.framing.value = False
        self.assertEqual(options.values(), (0.0, 1.0))
        options.motion.value = "true"
        self.assertEqual(options.values(), (0.0, 0.0))

    def test_bounds(self):
        options = DynamicOptions()
        for value, expected in ((50, 0.5), (150, 1.5), (10, 0.25), (999, 2.0), (float("nan"), 1.0), (True, 1.0)):
            options.motion_strength.value = value
            self.assertEqual(options.values()[1], expected)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
