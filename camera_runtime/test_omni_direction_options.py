"""OMNI DIRECTION options: body on at 360 degrees and the third-person sprint on by default, the crouch default set by
each mod, no third-person sprint switch in Omni Sprint, hidden two-value choices, hand-edited values back to
defaults."""
import pathlib
import sys
import types
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))


class Option:
    def __init__(self, identifier, value, *args, **kwargs):
        self.identifier, self.value = identifier, value
        self.limits, self.kwargs = args, kwargs


sys.modules['mods_base'] = types.SimpleNamespace(BoolOption=Option, SliderOption=Option)
from apex_camera_runtime.omni_direction_options import DASH, SLIDE, OmniDirectionOptions, OmniValues  # noqa: E402


class OptionsTests(unittest.TestCase):
    def test_defaults(self):
        options = OmniDirectionOptions(SLIDE)
        self.assertEqual(options.values(), OmniValues(True, True, True, False))
        self.assertEqual([option.identifier for option in options.options],
                         ["omni_body", "omni_angle", "omni_direction_sprint", "omni_crouch"])
        self.assertEqual(OmniDirectionOptions(DASH).values().dash, True)

    def test_choices_are_hidden_two_value_sliders(self):
        options = OmniDirectionOptions(DASH)
        for choice in (options.angle, options.crouch):
            self.assertEqual(choice.limits, (0, 1))
            self.assertTrue(choice.kwargs["is_hidden"] and choice.kwargs["is_integer"])

    def test_omni_sprint_has_no_third_person_sprint(self):
        options = OmniDirectionOptions(DASH, third_person_sprint=False)
        self.assertIsNone(options.sprint)
        self.assertEqual([option.identifier for option in options.options], ["omni_body", "omni_angle", "omni_crouch"])
        self.assertFalse(options.values().sprint)

    def test_switches(self):
        options = OmniDirectionOptions(SLIDE)
        options.angle.value, options.crouch.value = 1, 0.0
        self.assertEqual(options.values(), OmniValues(True, False, True, True))
        options.body.value = False
        self.assertEqual(options.values(), OmniValues(False, False, False, True))
        options.body.value, options.sprint.value = True, False
        self.assertFalse(options.values().sprint)

    def test_hand_edited_values_fall_back(self):
        options = OmniDirectionOptions(SLIDE)
        options.angle.value, options.crouch.value, options.body.value = 7, "dash", "yes"
        self.assertEqual(options.values(), OmniValues(False, True, False, False))


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(OptionsTests))
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    sys.exit(not result.wasSuccessful())
