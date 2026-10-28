"""Free Look's key: held, it starts after the hold time and lasts while held; pressed, each press turns it on or off;
aiming ends it until every key is up."""

import unittest

from apex_camera_runtime.free_look_keys import Trigger

FRAME_S = 1.0 / 60.0
HOLD_S = 0.20
HOLD, PRESS = True, False


def run(trigger, downs, holds=(HOLD, HOLD), frames=1):
    return [trigger.step(downs, holds, HOLD_S, FRAME_S) for _ in range(frames)]


class HoldTests(unittest.TestCase):
    def test_a_short_press_does_not_start(self):
        trigger = Trigger()
        self.assertFalse(any(run(trigger, (True, False), frames=int(HOLD_S / FRAME_S) - 1)))
        self.assertFalse(run(trigger, (False, False))[0])

    def test_held_long_enough_it_starts_and_lasts_until_released(self):
        trigger = Trigger()
        self.assertTrue(run(trigger, (True, False), frames=int(HOLD_S / FRAME_S) + 2)[-1])
        self.assertTrue(run(trigger, (True, False), frames=30)[-1])
        self.assertFalse(run(trigger, (False, False))[0])

    def test_the_controller_counts_as_much_as_the_keyboard(self):
        trigger = Trigger()
        self.assertTrue(run(trigger, (False, True), frames=int(HOLD_S / FRAME_S) + 2)[-1])


class PressTests(unittest.TestCase):
    def test_each_press_turns_it_on_then_off_at_once(self):
        trigger = Trigger()
        self.assertTrue(run(trigger, (True, False), (PRESS, HOLD))[0])
        self.assertTrue(run(trigger, (False, False), (PRESS, HOLD), frames=20)[-1])
        self.assertFalse(run(trigger, (True, False), (PRESS, HOLD))[0])
        self.assertFalse(run(trigger, (False, False), (PRESS, HOLD))[0])

    def test_keeping_the_key_down_is_one_press(self):
        trigger = Trigger()
        self.assertTrue(run(trigger, (True, False), (PRESS, HOLD), frames=30)[-1])


class AimTests(unittest.TestCase):
    def test_aiming_ends_a_hold_until_the_key_is_let_go(self):
        trigger = Trigger()
        run(trigger, (True, False), frames=int(HOLD_S / FRAME_S) + 2)
        trigger.cancel()
        self.assertFalse(any(run(trigger, (True, False), frames=60)))
        self.assertFalse(run(trigger, (False, False))[0])
        self.assertTrue(run(trigger, (True, False), frames=int(HOLD_S / FRAME_S) + 2)[-1])

    def test_aiming_ends_a_press_and_the_next_press_starts_again(self):
        trigger = Trigger()
        run(trigger, (True, False), (PRESS, HOLD))
        run(trigger, (False, False), (PRESS, HOLD))
        trigger.cancel()
        self.assertFalse(run(trigger, (False, False), (PRESS, HOLD))[0])
        self.assertTrue(run(trigger, (True, False), (PRESS, HOLD))[0])


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
