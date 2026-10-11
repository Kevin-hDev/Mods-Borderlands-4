"""The automatic camera distance: close after a moment in a low or narrow place, back after a moment out of it, never
for a doorway, holding while aiming, and the key always wins."""

import unittest

from apex_camera_runtime.camera_distance_auto import (CEILING_CM, ENTER_S, LEAVE_S, MARGIN_CM, WIDTH_CM, AutoDistance,
                                                      cramped)
from apex_camera_runtime.camera_distance_room import Reading

FRAME_S = 1 / 60


def run(auto, squeezed, seconds, allowed=True):
    shown = auto.close
    for _ in range(round(seconds / FRAME_S)):
        shown = auto.step(squeezed, allowed, FRAME_S)
    return shown


class CrampedTests(unittest.TestCase):
    def test_a_low_ceiling_or_a_narrow_passage_is_cramped(self):
        self.assertTrue(cramped(Reading(CEILING_CM - 1, 1000.0), False))
        self.assertTrue(cramped(Reading(1000.0, WIDTH_CM - 1), False))
        self.assertFalse(cramped(Reading(CEILING_CM, WIDTH_CM), False))

    def test_once_close_leaving_needs_the_margin(self):
        self.assertTrue(cramped(Reading(CEILING_CM + MARGIN_CM - 1, 1000.0), True))
        self.assertTrue(cramped(Reading(1000.0, WIDTH_CM + MARGIN_CM - 1), True))
        self.assertFalse(cramped(Reading(CEILING_CM + MARGIN_CM, WIDTH_CM + MARGIN_CM), True))


class AutoTests(unittest.TestCase):
    def setUp(self):
        self.auto = AutoDistance()

    def test_close_after_a_moment_in_a_cramped_place(self):
        self.assertFalse(run(self.auto, True, ENTER_S - 0.05))
        self.assertTrue(run(self.auto, True, 0.1))

    def test_a_doorway_moves_nothing(self):
        for _ in range(5):
            self.assertFalse(run(self.auto, True, ENTER_S - 0.05))
            self.assertFalse(run(self.auto, False, 0.1))

    def test_back_after_a_moment_out_and_a_short_opening_restarts_the_wait(self):
        run(self.auto, True, ENTER_S + 0.05)
        self.assertTrue(run(self.auto, False, LEAVE_S - 0.1))
        self.assertTrue(run(self.auto, True, 0.05))
        self.assertTrue(run(self.auto, False, LEAVE_S - 0.1))
        self.assertFalse(run(self.auto, False, 0.2))

    def test_aiming_or_no_reading_holds_and_restarts_the_delays(self):
        run(self.auto, True, ENTER_S - 0.05)
        self.assertFalse(run(self.auto, True, 0.5, allowed=False))
        self.assertFalse(run(self.auto, True, ENTER_S - 0.05))
        self.assertTrue(run(self.auto, True, 0.1))
        self.assertTrue(run(self.auto, False, 2.0, allowed=False))
        self.assertTrue(run(self.auto, None, 2.0))

    def test_the_key_in_a_cramped_place_wins_until_the_hunter_is_out(self):
        run(self.auto, True, ENTER_S + 0.05)
        self.auto.player_key()
        self.assertFalse(self.auto.close)
        self.assertTrue(self.auto.holding)
        self.assertFalse(run(self.auto, True, 3.0))
        self.assertFalse(run(self.auto, False, LEAVE_S + 0.05))
        self.assertFalse(self.auto.holding)
        self.assertTrue(run(self.auto, True, ENTER_S + 0.05))

    def test_the_key_out_in_the_open_waits_for_nothing(self):
        run(self.auto, False, 1.0)
        self.auto.player_key()
        self.assertFalse(self.auto.holding)
        self.assertTrue(run(self.auto, True, ENTER_S + 0.05))


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
