"""Speed FOV options: on, gain 7 and 0.4 s by default; hand-edited values fall back to the defaults."""
import sys
import types
import unittest


class Option:
    def __init__(self, identifier, value, *args, **kwargs):
        self.identifier, self.value = identifier, value


sys.modules['mods_base'] = types.SimpleNamespace(BoolOption=Option, SliderOption=Option)
from apex_camera_runtime.speed_fov_options import SpeedFovOptions  # noqa: E402


class OptionsTests(unittest.TestCase):
    def test_defaults(self):
        options = SpeedFovOptions()
        self.assertEqual(options.values(), (True, 7.0, 0.4))
        self.assertEqual([option.identifier for option in options.options],
                         ["speed_fov", "speed_fov_gain", "speed_fov_seconds"])

    def test_switch(self):
        options = SpeedFovOptions()
        for value in (False, "true", 1, None):
            options.enabled.value = value
            self.assertFalse(options.values()[0])

    def test_bounds(self):
        options = SpeedFovOptions()
        for value, expected in ((True, 7.0), ("5", 7.0), (float("nan"), 7.0), (float("inf"), 7.0),
                                (0, 1.0), (99, 30.0), (15, 15.0)):
            options.gain.value = value
            self.assertEqual(options.values()[1], expected)
        for value, expected in ((None, 0.4), (0, 0.1), (5, 2.0), (1.2, 1.2)):
            options.seconds.value = value
            self.assertEqual(options.values()[2], expected)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
