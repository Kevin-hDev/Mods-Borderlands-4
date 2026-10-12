"""The profiles' entry point: the draft shows over the profile switched on; saving writes the draft and switches its
profile on; a profile's key switches it on or back off, never while the window or a draft is open; the camera learns
of any change at its next frame; the file is read once, at the first use."""

import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

from profile_test_fixtures import values
from apex_camera_runtime import profile_store, profiles as profiles_module
from apex_camera_runtime.camera_distance import CLOSE, NORMAL
from apex_camera_runtime.profile_overlay import ProfiledSettings
from apex_camera_runtime.profile_store import Refused, Store
from apex_camera_runtime.profiles import Profiles


class Keys:
    def __init__(self):
        self.next, self.calls = None, []

    def pressed(self, pc, profiles):
        self.calls.append(("pressed", pc, tuple(profile.ident for profile in profiles)))
        ident, self.next = self.next, None
        return ident

    def pause(self):
        self.calls.append(("pause",))


def camera():
    return NS(fov_enabled=lambda: True, fov_value=lambda: 120.0, camera_distances=lambda: (150.0, 256.0, 400.0),
              framing_values=lambda: ((15, False), (60, False), (40, False)))


class ProfilesTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = pathlib.Path(folder.name) / profile_store.FILE_NAME
        self.notes, self.keys = [], Keys()
        self.store = Store(lambda: self.path, self.notes.append)
        self.profiles = Profiles(self.store, self.keys)

    def test_the_file_is_read_once_at_the_first_use(self):
        self.path.write_bytes(b'{"version": 1, "active": 1, "profiles": [{"id": 1, "name": "Combat", "fov": 100, '
                              b'"close": 1.4, "far": 3.2, "spacing": -40, "height": 25}]}')
        self.assertFalse(self.store.loaded)
        self.assertEqual(self.profiles.shown(), values(fov=100, close=1.4, far=3.2, spacing=-40, height=25))
        self.path.unlink()
        self.assertEqual(self.profiles.shown().fov, 100)
        self.assertIs(self.profiles.ready(), self.store)

    def test_nothing_shows_until_a_profile_is_on_or_the_window_open(self):
        self.assertIsNone(self.profiles.shown())
        self.assertEqual(self.profiles.distance(NORMAL), NORMAL)
        wrapped = self.profiles.wrap(camera())
        self.assertIsInstance(wrapped, ProfiledSettings)
        self.assertEqual(wrapped.fov_value(), 120.0)

    def test_a_new_draft_starts_from_what_the_camera_shows(self):
        self.profiles.open_new("Profile 1", camera(), 104.4)
        self.assertEqual(self.profiles.draft.values, values(fov=104, close=1.5, far=4.0, spacing=60, height=40))
        self.assertEqual((self.profiles.draft.name, self.profiles.draft.editing), ("Profile 1", None))
        self.assertEqual(self.profiles.shown(), self.profiles.draft.values)

    def test_a_new_draft_over_a_profile_starts_from_that_profile(self):
        self.store.load()
        self.store.put(None, "Combat", values(fov=90), activate=True)
        self.profiles.open_new("Profile 2", camera(), 104.4)
        self.assertEqual(self.profiles.draft.values, values(fov=90))

    def test_changes_show_at_once_and_cancel_goes_back(self):
        self.store.load()
        self.store.put(None, "Combat", values(fov=90), activate=True)
        self.profiles.open_new("Profile 2", camera(), None)
        self.profiles.change("fov", 130)
        self.profiles.change("close", 1.2)
        self.assertEqual(self.profiles.shown().fov, 130)
        self.assertEqual(self.profiles.distance(NORMAL), CLOSE)
        with self.assertRaises(ValueError):
            self.profiles.change("fov", 300)
        self.profiles.cancel()
        self.assertIsNone(self.profiles.draft)
        self.assertEqual(self.profiles.shown(), values(fov=90))
        self.assertEqual(self.profiles.distance(NORMAL), NORMAL)

    def test_saving_writes_the_draft_and_switches_its_profile_on(self):
        self.profiles.open_new("Profile 1", camera(), 100.0)
        self.profiles.draft.name, self.profiles.draft.keyboard = "Combat", "F5"
        self.profiles.change("height", 25)
        saved = self.profiles.save()
        self.assertEqual((saved.name, saved.keyboard, saved.values.height), ("Combat", "F5", 25))
        self.assertIsNone(self.profiles.draft)
        self.assertEqual(self.store.active, saved.ident)
        self.assertEqual(self.profiles.shown(), saved.values)
        reread = Store(lambda: self.path)
        reread.load()
        self.assertEqual((reread.profiles, reread.active), ((saved,), saved.ident))

    def test_a_refused_save_keeps_the_draft(self):
        self.profiles.open_new("  ", camera(), 100.0)
        with self.assertRaises(Refused) as caught:
            self.profiles.save()
        self.assertEqual(caught.exception.reason, "name_invalid")
        self.assertIsNotNone(self.profiles.draft)
        with self.assertRaises(Refused):
            Profiles(self.store, self.keys).save()

    def test_a_new_name_takes_the_first_free_number(self):
        self.assertEqual(self.profiles.free_name("Profil"), "Profil 1")
        self.store.put(None, "PROFIL 1", values())
        self.store.put(None, "Profil 3", values())
        self.assertEqual(self.profiles.free_name("Profil"), "Profil 2")
        self.assertEqual(self.profiles.free_name("Profile"), "Profile 1")

    def test_the_name_is_kept_as_typed_and_checked_at_save(self):
        self.profiles.open_new("Profile 1", camera(), 100.0)
        revision = self.profiles.revision
        self.profiles.rename("Combat ")
        self.assertEqual((self.profiles.draft.name, self.profiles.revision), ("Combat ", revision))
        self.assertEqual(self.profiles.save().name, "Combat")
        with self.assertRaises(Refused):
            self.profiles.rename("Sniper")

    def test_a_key_is_refused_as_it_is_chosen(self):
        self.store.load()
        combat = self.store.put(None, "Combat", values(), "F5", "Gamepad_DPad_Up")
        self.profiles.open_new("Profile 2", camera(), 100.0)
        self.profiles.set_keys("F6", "Gamepad_DPad_Down")
        self.assertEqual((self.profiles.draft.keyboard, self.profiles.draft.controller), ("F6", "Gamepad_DPad_Down"))
        for keys, reason in ((("F5", None), "key_taken"), ((None, "Gamepad_DPad_Up"), "key_taken"),
                             (("Gamepad_DPad_Left", None), "key_invalid"), ((None, "F7"), "key_invalid"),
                             (("Escape", None), "key_invalid")):
            with self.assertRaises(Refused) as caught:
                self.profiles.set_keys(*keys)
            self.assertEqual(caught.exception.reason, reason)
            self.assertEqual((self.profiles.draft.keyboard, self.profiles.draft.controller),
                             ("F6", "Gamepad_DPad_Down"))
        self.profiles.set_keys(None, "Gamepad_DPad_Down")
        self.assertIsNone(self.profiles.draft.keyboard)
        self.profiles.cancel()
        self.profiles.open_edit(combat.ident)
        # Its own keys are free to it.
        self.profiles.set_keys("F5", None)
        self.assertEqual(self.profiles.draft.keyboard, "F5")

    def test_profiles_are_available_unless_the_file_could_not_be_opened(self):
        self.assertTrue(self.profiles.available())
        with patch.object(pathlib.Path, "read_bytes", side_effect=PermissionError("locked")):
            self.path.write_bytes(b"{}")
            blocked = Profiles(Store(lambda: self.path, self.notes.append), self.keys)
            self.assertFalse(blocked.available())

    def test_modify_opens_the_profile_and_saves_over_it(self):
        self.store.load()
        combat = self.store.put(None, "Combat", values(fov=90), "F5")
        self.profiles.open_edit(combat.ident)
        self.assertEqual((self.profiles.draft.values, self.profiles.draft.name, self.profiles.draft.keyboard,
                          self.profiles.draft.editing), (values(fov=90), "Combat", "F5", combat.ident))
        self.profiles.draft.name = "Close"
        self.profiles.change("fov", 95)
        saved = self.profiles.save()
        self.assertEqual((saved.ident, saved.name, saved.values.fov, len(self.store.profiles)),
                         (combat.ident, "Close", 95, 1))
        with self.assertRaises(Refused):
            self.profiles.open_edit(42)

    def test_toggle_and_delete(self):
        self.store.load()
        first = self.store.put(None, "Combat", values(fov=90))
        second = self.store.put(None, "Sniper", values(fov=80))
        self.profiles.toggle(first.ident)
        self.assertEqual(self.profiles.shown().fov, 90)
        self.profiles.toggle(second.ident)
        self.assertEqual(self.profiles.shown().fov, 80)
        self.profiles.toggle(second.ident)
        self.assertIsNone(self.profiles.shown())
        self.profiles.toggle(first.ident)
        self.profiles.delete(first.ident)
        self.assertIsNone(self.profiles.shown())
        self.assertEqual([profile.ident for profile in self.store.profiles], [second.ident])

    def test_a_key_switches_its_profile_on_then_back_off(self):
        self.store.load()
        combat = self.store.put(None, "Combat", values(fov=90), "F5")
        self.keys.next = combat.ident
        self.profiles.sync("pc")
        self.assertEqual(self.store.active, combat.ident)
        self.keys.next = combat.ident
        self.profiles.sync("pc")
        self.assertIsNone(self.store.active)
        self.assertEqual(self.keys.calls[-1], ("pressed", "pc", (combat.ident,)))

    def test_keys_wait_while_a_draft_is_open(self):
        self.store.load()
        combat = self.store.put(None, "Combat", values(fov=90), "F5")
        self.keys.next = combat.ident
        self.profiles.open_new("Profile 2", camera(), None)
        self.profiles.sync("pc")
        self.assertEqual(self.keys.calls, [("pause",)])
        self.assertIsNone(self.store.active)

    def test_a_key_whose_save_fails_changes_nothing_and_says_so(self):
        self.store.load()
        combat = self.store.put(None, "Combat", values(fov=90), "F5")
        self.keys.next = combat.ident
        with patch.object(profile_store.os, "replace", side_effect=OSError("disk full")):
            self.profiles.sync("pc")
        self.assertIsNone(self.store.active)
        self.assertEqual(self.notes, ["camera profile key: save failed (OSError)"])

    def test_the_camera_learns_of_a_change_at_its_next_frame_only_once(self):
        self.assertFalse(self.profiles.sync("pc"))
        self.profiles.open_new("Profile 1", camera(), None)
        self.assertTrue(self.profiles.sync("pc"))
        self.assertFalse(self.profiles.sync("pc"))
        self.profiles.change("fov", 100)
        self.profiles.change("fov", 101)
        self.assertTrue(self.profiles.sync("pc"))
        self.assertFalse(self.profiles.sync("pc"))
        self.profiles.save()
        self.assertTrue(self.profiles.sync("pc"))

    def test_make_builds_the_runtime_profiles_without_reading_anything(self):
        made = profiles_module.make()
        self.assertIsInstance(made, Profiles)
        self.assertFalse(made.store.loaded)
        self.assertIsNone(made.keys.game)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ProfilesTests))
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    sys.exit(not result.wasSuccessful())
