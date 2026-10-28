"""Stored transition timing is shared, bounded and dormant while smoothing is off."""
import sys
import types
import unittest

class Option:
    def __init__(self, identifier, value, *bounds, **kwargs):
        self.identifier, self.value, self.default_value = identifier, value, value
        if bounds:
            self.min_value, self.max_value = bounds

sys.modules['mods_base'] = types.SimpleNamespace(BoolOption=Option, SliderOption=Option)

class Tests(unittest.TestCase):
    def test_orbit_switch_has_independent_toggle_and_shared_duration(self):
        from apex_camera_runtime.shoulder_transition_options import ShoulderTransitionOptions
        options = ShoulderTransitionOptions()
        self.assertTrue(options.orbit_smooth.value)
        options.duration.value = 0.75
        options.smooth.value = False
        self.assertEqual(options.orbit_seconds(), 0.75)
        options.orbit_smooth.value = False
        self.assertEqual(options.orbit_seconds(), 0)
        options.smooth.value = True
        self.assertEqual(options.seconds(), 0.75)

    def test_saved_duration_survives_disabled_animation(self):
        from apex_camera_runtime.shoulder_transition_options import ShoulderTransitionOptions
        options = ShoulderTransitionOptions()
        self.assertAlmostEqual(options.seconds(), 0.2)
        options.duration.value = 0.75
        options.smooth.value = False
        self.assertEqual(options.seconds(), 0)
        options.smooth.value = True
        self.assertEqual(options.seconds(), 0.75)

    def test_invalid_saved_durations_cannot_escape_bounds(self):
        from apex_camera_runtime.shoulder_transition_options import ShoulderTransitionOptions
        options = ShoulderTransitionOptions()
        for value, expected in ((float('nan'), 0.2), (True, 0.2), ('0.5', 0.2), (-10, 0.05), (200, 1.0)):
            options.duration.value = value
            self.assertEqual(options.seconds(), expected)

if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
