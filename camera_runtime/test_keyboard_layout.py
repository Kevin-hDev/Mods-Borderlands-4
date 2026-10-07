"""Default camera keys follow the keyboard: A or Q right of Tab, Hyphen or Six and E_AccentGrave or Seven on top."""

import unittest

from apex_camera_runtime.keyboard_layout import (RIGHT_OF_TAB, TOP_ROW_SEVEN, TOP_ROW_SIX, DEAD_KEY, key_at,
                                                 name)


def layout(code):
    asked = []

    def read(scan):
        asked.append(scan)
        return code
    return read, asked


class KeyAtTests(unittest.TestCase):
    def test_azerty_right_of_tab_keeps_kevins_a(self):
        read, asked = layout(ord("A"))
        self.assertEqual(key_at(RIGHT_OF_TAB, "Q", read), "A")
        self.assertEqual(asked, [RIGHT_OF_TAB])

    def test_qwerty_right_of_tab_is_q(self):
        self.assertEqual(key_at(RIGHT_OF_TAB, "Q", layout(ord("Q"))[0]), "Q")

    def test_azerty_top_row_six_and_seven_are_named_by_their_sign(self):
        self.assertEqual(key_at(TOP_ROW_SIX, "Six", layout(ord("-"))[0]), "Hyphen")
        self.assertEqual(key_at(TOP_ROW_SEVEN, "Seven", layout(0xE8)[0]), "E_AccentGrave")

    def test_qwerty_top_row_keeps_digit_names(self):
        self.assertEqual(key_at(TOP_ROW_SIX, "Six", layout(ord("6"))[0]), "Six")
        self.assertEqual(key_at(TOP_ROW_SEVEN, "Seven", layout(ord("7"))[0]), "Seven")

    def test_kevins_verified_top_row_names(self):
        self.assertEqual([name(code) for code in (ord("&"), 0xE9, ord('"'), ord("'"), ord("_"))],
                         ["Ampersand", "E_AccentAigu", "Quote", "Apostrophe", "Underscore"])

    def test_unknown_or_dead_signs_fall_back(self):
        for code in (0, ord("a"), 0x20AC, DEAD_KEY | ord("^"), -1, None, "A", 0x110000):
            self.assertEqual(key_at(TOP_ROW_SIX, "Six", layout(code)[0]), "Six")

    def test_windows_failing_falls_back(self):
        def broken(_scan):
            raise OSError("user32 unavailable")
        self.assertEqual(key_at(RIGHT_OF_TAB, "Q", broken), "Q")

    def test_this_machine_names_its_keys(self):
        for scan, fallback in ((RIGHT_OF_TAB, "Q"), (TOP_ROW_SIX, "Six"), (TOP_ROW_SEVEN, "Seven")):
            self.assertTrue(key_at(scan, fallback))


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
