"""Reject malformed settings before they can enter the grapple's calculations."""

import math
import unittest

import sdk_stubs

sdk_stubs.install()

from apex_grapple import settings  # noqa: E402


class SettingsValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        for option in settings.ALL:
            option.value = option.default_value

    def tearDown(self) -> None:
        self.setUp()

    def test_nonfinite_and_wrong_types_restore_each_slider_default(self) -> None:
        # Removing either the finite or type guard would let these reach physics.
        invalid = (float("nan"), float("inf"), -float("inf"), "1.7", "bad", None, True, False)
        for option in settings.ALL:
            if option.min_value is None:
                continue
            for value in invalid:
                with self.subTest(setting=option.identifier, value=value):
                    self.setUp()
                    option.value = value
                    warnings = settings.keep_in_bounds()
                    self.assertEqual(option.value, option.default_value)
                    self.assertIs(type(option.value), type(option.default_value))
                    self.assertTrue(math.isfinite(option.value))
                    self.assertTrue(warnings)
                    self.assertEqual(settings.keep_in_bounds(), [])

    def test_finite_extremes_clamp_to_each_slider_bounds(self) -> None:
        # Huge Python integers must be compared without overflowing float().
        for option in settings.ALL:
            if option.min_value is None:
                continue
            for value, expected in ((-1e300, option.min_value), (1e300, option.max_value),
                                    (-(10 ** 400), option.min_value), (10 ** 400, option.max_value)):
                with self.subTest(setting=option.identifier, side="low" if value < 0 else "high"):
                    self.setUp()
                    option.value = value
                    self.assertTrue(settings.keep_in_bounds())
                    self.assertEqual(option.value, expected)
                    self.assertEqual(settings.keep_in_bounds(), [])

    def test_valid_values_keep_their_value_and_type_without_rounding(self) -> None:
        for option in settings.ALL:
            values = (True, False) if option.min_value is None else (
                option.min_value, option.max_value, option.default_value,
                (option.min_value + option.max_value) / 2 + 0.123,
            )
            for value in values:
                with self.subTest(setting=option.identifier, value=value):
                    self.setUp()
                    option.value = value
                    self.assertEqual(settings.keep_in_bounds(), [])
                    self.assertIs(option.value, value)

    def test_switches_reject_numeric_and_string_truthiness(self) -> None:
        for option in settings.ALL:
            if option.min_value is not None:
                continue
            for value in (0, 1, 0.0, 1.0, "false", "true", "", None, float("nan")):
                with self.subTest(setting=option.identifier, value=value):
                    self.setUp()
                    option.value = value
                    self.assertTrue(settings.keep_in_bounds())
                    self.assertIs(option.value, option.default_value)

    def test_range_relationship_runs_after_individual_validation(self) -> None:
        # The prior relationship remains 100 cm below range once inputs are safe.
        cases = ((500, 500, 500, 400), (500, 1e300, 500, 400),
                 (None, float("nan"), 3000, 200), (float("nan"), 500, 3000, 500),
                 (-1e300, 1000, 500, 400))
        for reach, punch, expected_reach, expected_punch in cases:
            with self.subTest(reach=reach, punch=punch):
                self.setUp()
                settings.grapple_range.value = reach
                settings.punch_range.value = punch
                self.assertTrue(settings.keep_in_bounds())
                self.assertEqual(settings.grapple_range.value, expected_reach)
                self.assertEqual(settings.punch_range.value, expected_punch)
                self.assertEqual(settings.keep_in_bounds(), [])

    def test_warnings_do_not_echo_untrusted_values(self) -> None:
        settings.pull_strength.value = "sensitive-user-input"
        warnings = settings.keep_in_bounds()
        self.assertTrue(warnings)
        self.assertNotIn("sensitive-user-input", " ".join(warnings))
        self.assertTrue(all(isinstance(line, str) for line in warnings))


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(SettingsValidationTests)
    )
    print("RESULTAT:", "TOUS LES TESTS PASSENT" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(0 if result.wasSuccessful() else 1)
