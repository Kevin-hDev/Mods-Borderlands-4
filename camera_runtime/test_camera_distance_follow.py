"""Each frame, the automatic distance reads the guard's room: close in a cramped place unless the close distance is
already chosen or the hunter aims, a gentler glide for its own moves, each move logged with the room."""

import unittest
from types import SimpleNamespace as NS

from apex_camera_runtime.camera_distance import CLOSE, FAR, NORMAL, SECONDS
from apex_camera_runtime.camera_distance_auto import ENTER_S, GLIDE_S, LEAVE_S
from apex_camera_runtime.camera_distance_follow import CameraDistanceFollow
from apex_camera_runtime.camera_distance_room import Reading

FRAME_NS = 16_666_667
LOW = Reading(100.0, 1000.0)
OPEN = Reading(800.0, 800.0)


class Room:
    def __init__(self):
        self.reading = OPEN

    def take(self):
        return self.reading


class FollowTests(unittest.TestCase):
    def setUp(self):
        self.room, self.lines, self.now = Room(), [], 0
        self.controller = NS(bridge=NS(collision=NS(room=self.room)), log=self.lines.append)
        self.follow = CameraDistanceFollow()

    def frames(self, seconds, chosen=FAR, aiming=False):
        shown = None
        for _ in range(round(seconds * 1e9 / FRAME_NS)):
            self.now += FRAME_NS
            shown = self.follow.close(self.controller, chosen, aiming, self.now)
        return shown

    def test_a_low_ceiling_brings_the_close_distance_with_a_gentler_glide(self):
        self.frames(0.5)
        self.room.reading = LOW
        self.assertTrue(self.frames(ENTER_S + 0.05))
        self.assertEqual(self.follow.glide_s, GLIDE_S)
        self.assertIn("automatic distance: close (ceiling 100 cm, narrowest 1000 cm)", self.lines)
        self.frames(GLIDE_S + 0.05)
        self.assertEqual(self.follow.glide_s, SECONDS)
        self.room.reading = OPEN
        self.assertFalse(self.frames(LEAVE_S + 0.05))
        self.assertIn("automatic distance: chosen distance back (ceiling 800 cm, narrowest 800 cm)", self.lines)

    def test_already_close_or_aiming_nothing_moves(self):
        self.room.reading = LOW
        self.assertFalse(self.frames(2.0, chosen=CLOSE))
        self.assertFalse(self.frames(2.0, aiming=True))
        self.assertTrue(self.frames(ENTER_S + 0.05, chosen=NORMAL))

    def test_without_a_room_the_camera_holds(self):
        self.controller.bridge = NS()
        self.assertFalse(self.frames(1.0))
        self.room.reading = None
        self.controller.bridge = NS(collision=NS(room=self.room))
        self.assertFalse(self.frames(1.0))

    def test_the_key_ends_the_glide_and_wins(self):
        self.room.reading = LOW
        self.frames(ENTER_S + 0.05)
        self.follow.player_key()
        self.assertEqual(self.follow.glide_s, SECONDS)
        self.assertFalse(self.frames(2.0))

    def test_switched_off_the_close_distance_glides_back_and_nothing_moves(self):
        self.room.reading = LOW
        self.frames(ENTER_S + 0.05)
        self.now += FRAME_NS
        self.assertFalse(self.follow.close(self.controller, FAR, False, self.now, False))
        self.assertEqual(self.follow.glide_s, GLIDE_S)
        self.assertEqual(self.lines[-1], "automatic distance: switched off, chosen distance back")
        for _ in range(120):
            self.now += FRAME_NS
            self.assertFalse(self.follow.close(self.controller, FAR, False, self.now, False))
        self.assertEqual(self.lines[-1], "automatic distance: switched off, chosen distance back")

    def test_reset_forgets_a_move_under_way(self):
        self.room.reading = LOW
        self.frames(ENTER_S + 0.05)
        self.follow.reset()
        self.assertFalse(self.follow.auto.close)
        self.assertEqual(self.follow.glide_s, SECONDS)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
