"""The camera profiles' file: read tolerantly, written strictly, before memory; a file that does not read whole is set
aside at the next save, never overwritten; names, keys and the count are bounded."""

import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

from profile_test_fixtures import values
from apex_camera_runtime import profile_entry, profile_store as ps
from apex_camera_runtime.profile_store import Profile, Refused, Store


class StoreTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = pathlib.Path(folder.name)
        self.path = self.folder / ps.FILE_NAME
        self.notes = []

    def store(self):
        store = Store(lambda: self.path, self.notes.append)
        store.load()
        return store

    def written(self):
        return json.loads(self.path.read_bytes().decode("utf-8"))

    def refused(self, reason, action, *args, **kwargs):
        with self.assertRaises(Refused) as caught:
            action(*args, **kwargs)
        self.assertEqual(caught.exception.reason, reason)

    def test_no_file_is_no_profile_and_no_note(self):
        store = self.store()
        self.assertTrue(store.loaded)
        self.assertEqual((store.profiles, store.active, self.notes), ((), None, []))
        self.assertFalse(self.path.exists())

    def test_a_saved_profile_reads_back_whole_in_another_store(self):
        store = self.store()
        combat = store.put(None, "  Été Combat ", values(fov=100, close=1.4), "F5", "Gamepad_DPad_Up")
        self.assertEqual(combat, Profile(1, "Été Combat", values(fov=100, close=1.4), "F5", "Gamepad_DPad_Up"))
        sniper = store.put(None, "Sniper", values(spacing=60), activate=True)
        self.assertEqual((sniper.ident, store.active), (2, 2))
        raw = self.path.read_bytes()
        self.assertNotIn(b"\r\n", raw)
        self.assertEqual(self.written()["version"], ps.VERSION)
        self.assertEqual(self.written()["profiles"][0], {
            "id": 1, "name": "Été Combat", "fov": 100, "close": 1.4, "far": 3.6, "spacing": 10, "height": 0,
            "keyboard": "F5", "controller": "Gamepad_DPad_Up"})
        again = self.store()
        self.assertEqual((again.profiles, again.active), ((combat, sniper), 2))
        self.assertEqual(self.notes, [])

    def test_update_delete_and_switch(self):
        store = self.store()
        store.put(None, "Combat", values())
        store.put(None, "Sniper", values())
        renamed = store.put(1, "Close", values(height=25), "F7")
        self.assertEqual(store.profile(1), renamed)
        self.assertEqual([profile.ident for profile in store.profiles], [1, 2])
        store.activate(1)
        store.delete(1)
        self.assertEqual(([profile.ident for profile in store.profiles], store.active), ([2], None))
        store.activate(2)
        store.activate(None)
        self.assertEqual(self.store().active, None)
        third = store.put(None, "Third", values())
        self.assertEqual(third.ident, 3)

    def test_names_are_bounded_and_unique(self):
        store = self.store()
        store.put(None, "Combat", values())
        for bad in ("", "   ", "x" * (profile_entry.MAX_NAME + 1), "<script>", "a/b", None, 5, "---"):
            with self.subTest(name=bad):
                self.refused("name_invalid", store.put, None, bad, values())
        self.assertEqual(store.put(None, "x" * profile_entry.MAX_NAME, values()).name, "x" * profile_entry.MAX_NAME)
        self.assertEqual(store.put(None, "L'été - 2_b’", values()).name, "L'été - 2_b’")
        self.refused("name_taken", store.put, None, "COMBAT", values())
        self.assertEqual(store.put(1, "combat", values()).name, "combat")

    def test_keys_are_checked_and_never_shared_by_two_profiles(self):
        store = self.store()
        store.put(None, "Combat", values(), "F5", "Gamepad_DPad_Up")
        self.refused("key_taken", store.put, None, "Sniper", values(), "F5")
        self.refused("key_taken", store.put, None, "Sniper", values(), None, "Gamepad_DPad_Up")
        for keyboard, controller in (("Escape", None), ("LeftMouseButton", None), ("Gamepad_A", None),
                                     (None, "F6"), (None, "Gamepad_LeftX"), ("bad key", None)):
            with self.subTest(keyboard=keyboard, controller=controller):
                self.refused("key_invalid", store.put, None, "Sniper", values(), keyboard, controller)
        self.assertEqual(store.put(1, "Combat", values(), "F5", None).keyboard, "F5")

    def test_values_are_checked_again_at_the_door(self):
        store = self.store()
        with self.assertRaises(ValueError):
            store.put(None, "Combat", values(fov=500))
        self.assertEqual(store.profiles, ())

    def test_ten_profiles_at_most(self):
        store = self.store()
        for index in range(ps.MAX_PROFILES):
            store.put(None, f"Profile {index}", values())
        self.refused("profiles_full", store.put, None, "One more", values())
        self.assertEqual(len(store.profiles), ps.MAX_PROFILES)

    def test_an_unknown_profile_is_refused(self):
        store = self.store()
        self.refused("profile_unknown", store.put, 4, "Combat", values())
        self.refused("profile_unknown", store.delete, 4)
        self.refused("profile_unknown", store.activate, 4)

    def test_a_save_that_fails_changes_nothing(self):
        store = self.store()
        store.put(None, "Combat", values())
        before = self.path.read_bytes()
        with patch.object(ps.os, "replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                store.put(None, "Sniper", values())
            with self.assertRaises(OSError):
                store.activate(1)
        self.assertEqual(([profile.name for profile in store.profiles], store.active), (["Combat"], None))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(sorted(path.name for path in self.folder.iterdir()), [ps.FILE_NAME])

    def test_an_unreadable_file_is_set_aside_at_the_next_save_never_overwritten(self):
        broken = b'{"version": 1, "profiles": [ broken'
        self.path.write_bytes(broken)
        store = self.store()
        self.assertEqual(store.profiles, ())
        self.assertEqual(len(self.notes), 1)
        self.assertEqual(self.path.read_bytes(), broken)
        store.put(None, "Combat", values())
        self.assertEqual((self.folder / "camera_profiles.unreadable.json").read_bytes(), broken)
        self.assertEqual([entry["name"] for entry in self.written()["profiles"]], ["Combat"])
        store.put(None, "Sniper", values())
        self.assertEqual((self.folder / "camera_profiles.unreadable.json").read_bytes(), broken)

        self.path.write_bytes(b"[]")
        self.store().put(None, "Combat", values())
        self.assertEqual((self.folder / "camera_profiles.unreadable-2.json").read_bytes(), b"[]")

    def test_set_aside_names_are_bounded(self):
        for name in ps.ASIDE_NAMES:
            (self.folder / name).write_bytes(b"old")
        self.path.write_bytes(b"not json")
        store = self.store()
        with self.assertRaises(OSError):
            store.put(None, "Combat", values())
        self.assertEqual(self.path.read_bytes(), b"not json")

    def test_a_bad_profile_is_left_out_and_the_file_kept_aside(self):
        good = {"id": 1, "name": "Combat", "fov": 100, "close": 1.4, "far": 3.2, "spacing": -40, "height": 25,
                "keyboard": "F5", "controller": None}
        entries = [good, dict(good, id=2, name="Bad", fov=500), dict(good, id=3, name="Twin", keyboard="F5"),
                   dict(good, id=1, name="Same id", keyboard=None), "nonsense", dict(good, id=True, name="Bool")]
        raw = json.dumps({"version": 1, "active": 3, "profiles": entries}).encode("utf-8")
        self.path.write_bytes(raw)
        store = self.store()
        self.assertEqual(([profile.name for profile in store.profiles], store.active), (["Combat"], None))
        self.assertEqual(len(self.notes), len(entries) - 1)
        self.assertTrue(all("invalid" in note or "profile" in note for note in self.notes))
        store.activate(1)
        self.assertEqual((self.folder / "camera_profiles.unreadable.json").read_bytes(), raw)

    def test_another_version_or_too_many_profiles_are_kept_aside(self):
        entry = {"id": 1, "name": "Combat", "fov": 100, "close": 1.4, "far": 3.2, "spacing": -40, "height": 25}
        newer = json.dumps({"version": 2, "active": 1, "profiles": [entry], "colours": "x"}).encode("utf-8")
        self.path.write_bytes(newer)
        store = self.store()
        self.assertEqual(([profile.name for profile in store.profiles], store.active), (["Combat"], 1))
        store.activate(None)
        self.assertEqual((self.folder / "camera_profiles.unreadable.json").read_bytes(), newer)

        many = [dict(entry, id=index, name=f"P{index}") for index in range(1, ps.MAX_PROFILES + 3)]
        self.path.write_bytes(json.dumps({"version": 1, "active": None, "profiles": many}).encode("utf-8"))
        store = self.store()
        self.assertEqual(len(store.profiles), ps.MAX_PROFILES)
        store.activate(1)
        self.assertTrue((self.folder / "camera_profiles.unreadable-2.json").exists())

    def test_an_absurd_number_or_nesting_is_left_out_never_a_failed_read(self):
        good = {"id": 1, "name": "Combat", "fov": 100, "close": 1.4, "far": 3.2, "spacing": -40, "height": 25}
        huge = ('{"version": 1, "active": null, "profiles": [{"id": 2, "name": "Huge", "fov": 1' + "0" * 400 + "}, "
                + json.dumps(good) + "]}").encode("utf-8")
        self.path.write_bytes(huge)
        store = self.store()
        self.assertEqual([profile.name for profile in store.profiles], ["Combat"])
        store.activate(1)
        self.assertEqual((self.folder / "camera_profiles.unreadable.json").read_bytes(), huge)

        deep = b"[" * 100_000 + b"]" * 100_000
        self.path.write_bytes(deep)
        store = self.store()
        self.assertEqual(store.profiles, ())
        store.put(None, "Combat", values())
        self.assertEqual((self.folder / "camera_profiles.unreadable-2.json").read_bytes(), deep)

    def test_a_file_saved_with_a_byte_order_mark_reads_whole(self):
        entry = {"id": 1, "name": "Combat", "fov": 100, "close": 1.4, "far": 3.2, "spacing": -40, "height": 25}
        self.path.write_bytes(b"\xef\xbb\xbf" + json.dumps({"version": 1, "active": 1, "profiles": [entry]}).encode())
        store = self.store()
        self.assertEqual(([profile.name for profile in store.profiles], store.active, self.notes), (["Combat"], 1, []))

    def test_the_file_set_aside_stays_in_place_until_the_new_one_is_written(self):
        self.path.write_bytes(b"not json")
        store = self.store()
        with patch.object(pathlib.Path, "write_bytes", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                store.put(None, "Combat", values())
        self.assertEqual(self.path.read_bytes(), b"not json")
        self.assertEqual(store.profiles, ())
        store.put(None, "Combat", values())
        self.assertEqual((self.folder / "camera_profiles.unreadable.json").read_bytes(), b"not json")
        self.assertEqual(sorted(path.name for path in self.folder.iterdir()),
                         [ps.FILE_NAME, "camera_profiles.unreadable.json"])

    def test_a_new_profile_never_takes_an_identifier_the_next_load_refuses(self):
        entry = {"id": ps.MAX_ID, "name": "Combat", "fov": 100, "close": 1.4, "far": 3.2, "spacing": -40, "height": 25}
        self.path.write_bytes(json.dumps({"version": 1, "active": None, "profiles": [entry]}).encode())
        sniper = self.store().put(None, "Sniper", values(), activate=True)
        again = self.store()
        self.assertEqual(([profile.name for profile in again.profiles], again.active),
                         (["Combat", "Sniper"], sniper.ident))

    def test_a_file_that_cannot_be_opened_is_never_written_over(self):
        kept = b'{"version": 1, "active": null, "profiles": []}'
        self.path.write_bytes(kept)
        with patch.object(pathlib.Path, "read_bytes", side_effect=PermissionError("locked")):
            store = self.store()
        self.assertEqual(len(self.notes), 1)
        with self.assertRaises(OSError):
            store.put(None, "Combat", values())
        self.assertEqual(self.path.read_bytes(), kept)
        self.assertEqual(store.profiles, ())

    def test_without_a_settings_folder_the_profiles_stay_off_and_nothing_is_written(self):
        def missing():
            raise ImportError("no SETTINGS_DIR")
        store = Store(missing, self.notes.append)
        store.load()
        self.assertEqual(self.notes, ["camera profiles: settings folder unavailable (ImportError)"])
        with self.assertRaises(OSError):
            store.put(None, "Combat", values())
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_the_default_path_is_in_the_sdk_settings_folder(self):
        with patch.dict(sys.modules["mods_base"].__dict__, {"SETTINGS_DIR": str(self.folder)}):
            self.assertEqual(ps.default_path(), self.folder / "camera_profiles.json")
        self.assertFalse(os.path.exists(self.folder / "camera_profiles.json.tmp"))


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(StoreTests))
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    sys.exit(not result.wasSuccessful())
