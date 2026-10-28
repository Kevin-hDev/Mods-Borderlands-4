"""The optic zoom key: a new press goes to the next zoom only while an aim with two or more ticked zooms is held at
the shoulder; a key held into the aim waits for its release, and one failure stops the key without touching the
aim."""

import unittest
from types import SimpleNamespace as NS

from apex_camera_runtime.ads_optic import OpticLink
from apex_camera_runtime.sniper_zoom import MAX_KEYS, REPORT_FRAMES, SniperZoom


class Native:
    def __init__(self):
        self.calls = []
        self.error = None

    def stats(self):
        return NS(fov_before=90.0, fov_after=33.4, zoom_scale=1 / 3)

    def set_optic(self, generation, scale):
        if self.error is not None:
            raise self.error
        self.calls.append((generation, scale))


class ZoomKeyTests(unittest.TestCase):
    def setUp(self):
        self.down = set()
        self.logs, self.made = [], []
        self.pc = NS(IsInputKeyDown=lambda key: key.name in self.down)
        self.native = Native()
        self.optic = OpticLink()
        self.optic.category, self.optic.ticked, self.optic.native_optics = 5, (3, 6), True
        self.controller = NS(ads=NS(optic=self.optic, native=self.native))
        self.keys = ("A", "Gamepad_LeftThumbstick")
        self.settings = NS(sniper_zoom_keys=lambda: self.keys)
        self.unit = SniperZoom(lambda: (lambda name: self.made.append(name) or NS(name=name), self.logs.append))

    def aim(self):
        self.optic.publish(self.native, 1)

    def frame(self, *down):
        self.down = set(down)
        self.unit.sync(self.settings, self.pc, self.controller)

    def test_a_new_press_while_aiming_goes_to_the_next_zoom(self):
        self.aim()
        self.frame()
        self.frame("A")
        self.frame("A")
        self.frame()
        self.frame("Gamepad_LeftThumbstick")
        self.assertEqual(self.native.calls, [(1, 1 / 3), (1, 1 / 6), (1, 1 / 3)])
        self.assertEqual(self.logs, ["optic zoom x6", "optic zoom x3"])

    def test_nothing_without_an_aim_of_ours(self):
        self.frame("A")
        self.frame()
        self.frame("A")
        self.assertEqual(self.native.calls, [])
        self.assertEqual(self.made, [])

    def test_the_view_of_an_aim_start_and_of_each_zoom_goes_to_the_log_once_settled(self):
        self.pc.PlayerCameraManager = NS(GetFOVAngle=lambda: 33.4)
        self.aim()
        for _ in range(REPORT_FRAMES):
            self.frame()
        self.frame("A")
        for _ in range(REPORT_FRAMES + 5):
            self.frame()
        line = "optic view x{}: base 90.0, ours 33.4 (scale 0.333), shown 33.4"
        self.assertEqual(self.logs, [line.format(3), "optic zoom x6", line.format(6)])

    def test_a_failed_view_line_stops_alone(self):
        self.aim()
        for _ in range(REPORT_FRAMES):
            self.frame()
        self.frame("A")
        self.assertEqual(self.logs, ["optic view line stopped for the session: AttributeError", "optic zoom x6"])

    def test_a_single_zoom_has_nothing_to_switch_to(self):
        self.optic.category, self.optic.ticked = 1, (1,)
        self.aim()
        self.frame()
        self.frame("A")
        self.assertEqual((self.native.calls, self.logs), ([(1, 0.75)], []))

    def test_x1_is_one_of_the_zooms(self):
        self.optic.category, self.optic.ticked = 4, (1, 3)
        self.aim()
        self.frame()
        self.frame("A")
        self.frame()
        self.frame("A")
        self.assertEqual(self.native.calls, [(1, 0.75), (1, 1 / 3), (1, 0.75)])
        self.assertEqual(self.logs, ["optic zoom x3", "optic zoom x1"])

    def test_a_key_held_into_the_aim_waits_for_its_release(self):
        self.frame("A")
        self.aim()
        self.frame("A")
        self.assertEqual(self.native.calls, [(1, 1 / 3)])
        self.frame()
        self.frame("A")
        self.assertEqual(self.native.calls[-1], (1, 1 / 6))

    def test_after_letting_go_of_the_aim_the_key_does_nothing(self):
        self.aim()
        self.frame()
        self.optic.release(self.native)
        self.frame("A")
        self.assertEqual(self.native.calls, [(1, 1 / 3), (1, 1.0)])

    def test_an_older_mod_without_zoom_keys_changes_nothing(self):
        self.aim()
        self.settings = NS()
        self.frame()
        self.frame("A")
        self.assertEqual(self.native.calls, [(1, 1 / 3)])

    def test_a_cleared_key_is_skipped(self):
        self.keys = (None, "Gamepad_LeftThumbstick")
        self.aim()
        self.frame()
        self.frame("Gamepad_LeftThumbstick")
        self.assertEqual(self.made, ["Gamepad_LeftThumbstick"])
        self.assertEqual(self.native.calls[-1], (1, 1 / 6))

    def test_a_failure_stops_the_key_for_the_session_and_says_so(self):
        self.aim()
        self.frame()
        self.native.error = RuntimeError("Aiming optic unavailable")
        self.frame("A")
        self.native.error = None
        self.frame()
        self.frame("A")
        self.assertEqual(self.native.calls, [(1, 1 / 3)])
        self.assertEqual(self.logs, ["sniper zoom key stopped for the session: RuntimeError"])

    def test_the_key_cache_is_bounded(self):
        self.aim()
        for index in range(MAX_KEYS + 3):
            self.keys = (f"Key{index}", None)
            self.frame()
        self.assertLessEqual(len(self.unit.keys), MAX_KEYS)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ZoomKeyTests))
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
