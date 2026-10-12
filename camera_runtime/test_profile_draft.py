"""The profile window's draft: each change is checked against its slider's bounds; moving the close or far distance
shows that distance until the player's distance key picks another one."""

import sys
import unittest

from profile_test_fixtures import values
from apex_camera_runtime.camera_distance import CLOSE, FAR, NORMAL
from apex_camera_runtime.profile_draft import Draft


class DraftTests(unittest.TestCase):
    def test_a_new_draft_keeps_what_it_was_given(self):
        draft = Draft(values(fov=100), "Profile 1")
        self.assertEqual((draft.values, draft.name, draft.keyboard, draft.controller, draft.editing),
                         (values(fov=100), "Profile 1", None, None, None))
        edit = Draft(values(), "Combat", "F5", "Gamepad_DPad_Up", editing=3)
        self.assertEqual((edit.keyboard, edit.controller, edit.editing), ("F5", "Gamepad_DPad_Up", 3))

    def test_a_change_is_checked_and_a_refused_one_changes_nothing(self):
        draft = Draft(values(), "Profile 1")
        draft.change("height", 25)
        self.assertEqual(draft.values, values(height=25))
        for field, bad in (("height", 101), ("fov", 69), ("spacing", True), ("zoom", 15)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                draft.change(field, bad)
        self.assertEqual(draft.values, values(height=25))

    def test_without_a_distance_change_the_players_distance_shows(self):
        draft = Draft(values(), "Profile 1")
        draft.change("fov", 100)
        for chosen in (CLOSE, NORMAL, FAR):
            self.assertEqual(draft.distance(chosen), chosen)

    def test_tuning_a_distance_shows_it_until_the_distance_key_changes_the_choice(self):
        draft = Draft(values(), "Profile 1")
        draft.change("close", 1.4)
        self.assertEqual(draft.distance(NORMAL), CLOSE)
        self.assertEqual(draft.distance(NORMAL), CLOSE)
        draft.change("far", 4.5)
        self.assertEqual(draft.distance(NORMAL), FAR)
        self.assertEqual(draft.distance(CLOSE), CLOSE)
        self.assertEqual(draft.distance(NORMAL), NORMAL)
        draft.change("far", 4.6)
        self.assertEqual(draft.distance(CLOSE), FAR)

    def test_a_refused_distance_change_does_not_move_the_camera(self):
        draft = Draft(values(), "Profile 1")
        with self.assertRaises(ValueError):
            draft.change("close", 9.0)
        self.assertEqual(draft.distance(NORMAL), NORMAL)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DraftTests))
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    sys.exit(not result.wasSuccessful())
