"""The profiles' keys: a new press gives that profile; a key already down at the first reading, or after a pause,
waits for its release; one failure stops the keys for the session with one line; the key cache is bounded."""

import sys
import unittest
from types import SimpleNamespace as NS

from profile_test_fixtures import values
from apex_camera_runtime.profile_keys import MAX_KEYS, ProfileKeys
from apex_camera_runtime.profile_store import Profile


class KeyTests(unittest.TestCase):
    def setUp(self):
        self.down, self.made, self.logs = set(), [], []
        self.pc = NS(IsInputKeyDown=lambda key: key.name in self.down)
        self.keys = ProfileKeys(lambda: (lambda name: self.made.append(name) or NS(name=name), self.logs.append))
        self.profiles = (Profile(1, "Combat", values(), "F5", "Gamepad_DPad_Up"), Profile(2, "Sniper", values(), "F6"),
                         Profile(3, "Bare", values()))

    def read(self, *down):
        self.down = set(down)
        return self.keys.pressed(self.pc, self.profiles)

    def test_a_new_press_gives_its_profile_once(self):
        self.assertIsNone(self.read())
        self.assertEqual(self.read("F5"), 1)
        self.assertIsNone(self.read("F5"))
        self.assertIsNone(self.read())
        self.assertEqual(self.read("Gamepad_DPad_Up"), 1)
        self.assertEqual(self.read("Gamepad_DPad_Up", "F6"), 2)

    def test_a_key_down_at_the_first_reading_or_after_a_pause_waits_for_its_release(self):
        self.assertIsNone(self.read("F5"))
        self.assertIsNone(self.read("F5"))
        self.assertIsNone(self.read())
        self.assertEqual(self.read("F5"), 1)
        self.keys.pause()
        self.assertIsNone(self.read("F5"))
        self.assertIsNone(self.read())
        self.assertEqual(self.read("F6"), 2)

    def test_no_player_or_no_key_reads_nothing(self):
        self.assertIsNone(self.keys.pressed(None, self.profiles))
        self.assertIsNone(self.keys.pressed(self.pc, (Profile(3, "Bare", values()),)))
        self.assertEqual(self.made, [])

    def test_the_game_is_asked_only_once_a_key_exists(self):
        loads = []
        keys = ProfileKeys(lambda: loads.append(1) or (lambda name: NS(name=name), self.logs.append))
        keys.pressed(self.pc, ())
        self.assertEqual(loads, [])
        keys.pressed(self.pc, self.profiles)
        keys.pressed(self.pc, self.profiles)
        self.assertEqual(loads, [1])

    def test_one_failure_stops_the_keys_for_the_session_with_one_line(self):
        self.read()

        def broken(_key):
            raise RuntimeError("input gone")
        self.pc.IsInputKeyDown = broken
        self.assertIsNone(self.read("F5"))
        self.assertIsNone(self.read("F5"))
        self.assertEqual(self.logs, ["profile keys stopped for the session: RuntimeError"])
        self.pc.IsInputKeyDown = lambda key: key.name in self.down
        self.assertIsNone(self.read("F6"))

    def test_the_key_cache_is_bounded(self):
        for index in range(MAX_KEYS + 5):
            self.profiles = (Profile(1, "Combat", values(), f"Key{index}"),)
            self.read()
        self.assertLessEqual(len(self.keys.keys), MAX_KEYS)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(KeyTests))
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    sys.exit(not result.wasSuccessful())
