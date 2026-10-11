"""The room around the hunter: one sweep per frame from its head, up then around; the ceiling and the narrowest
passage once every direction is known, nothing while stale."""

import math
import unittest

from apex_camera_runtime.camera_distance_room import (DIRECTIONS, HEAD_CM, MAX_AGE, REACH_CM, CameraDistanceRoom,
                                                      Reading)

HUNTER = (100.0, -50.0, 20.0)
HEAD = (100.0, -50.0, 20.0 + HEAD_CM)


class Sweep:
    """Free distance per direction, found from the sweep's end."""

    def __init__(self, free):
        self.free, self.calls, self.fail = free, [], False

    def distance(self, actor, start, end):
        self.calls.append((actor, start, end))
        if self.fail:
            raise ValueError("invalid initial collision depth")
        direction = tuple((e - s) / REACH_CM for s, e in zip(start, end))
        # cos 90° is not exactly 0: the nearest direction is the one swept.
        return self.free[min(range(len(DIRECTIONS)), key=lambda i: math.dist(DIRECTIONS[i], direction))]


def room_with(free):
    room, sweep = CameraDistanceRoom(), Sweep(free)
    for _ in DIRECTIONS:
        room.record(sweep, "hunter", HUNTER)
    return room, sweep


class RoomTests(unittest.TestCase):
    def test_each_frame_sweeps_one_direction_from_the_head(self):
        room, sweep = room_with([REACH_CM] * len(DIRECTIONS))
        self.assertEqual(len(sweep.calls), len(DIRECTIONS))
        self.assertTrue(all(actor == "hunter" and start == HEAD for actor, start, _end in sweep.calls))
        self.assertEqual(sweep.calls[0][2], (100.0, -50.0, 20.0 + HEAD_CM + REACH_CM))
        for (_actor, start, end), direction in zip(sweep.calls, DIRECTIONS):
            self.assertAlmostEqual(math.dist(start, end), REACH_CM)
            self.assertTrue(all(math.isclose(e - s, REACH_CM * d, abs_tol=1e-9)
                                for s, e, d in zip(start, end, direction)))

    def test_nothing_until_every_direction_is_known(self):
        room, sweep = CameraDistanceRoom(), Sweep([REACH_CM] * len(DIRECTIONS))
        for _ in range(len(DIRECTIONS) - 1):
            room.record(sweep, "hunter", HUNTER)
            self.assertIsNone(room.take())
        room.record(sweep, "hunter", HUNTER)
        self.assertEqual(room.take(), Reading(REACH_CM, 2 * REACH_CM))

    def test_the_narrowest_passage_adds_opposite_sides(self):
        # Up 120; around: east 90, west 110 make a 200 cm corridor; the other lines are open.
        free = [120.0, 90.0, 400.0, 400.0, 400.0, 110.0, 400.0, 400.0, 400.0]
        room, _sweep = room_with(free)
        self.assertEqual(room.take(), Reading(120.0, 200.0))

    def test_one_wall_alone_leaves_the_passage_wide(self):
        free = [400.0, 30.0] + [400.0] * 7
        room, _sweep = room_with(free)
        self.assertEqual(room.take().narrowest, 430.0)

    def test_a_sweep_from_inside_a_wall_keeps_that_directions_last_width(self):
        room, sweep = room_with([150.0] + [400.0] * 8)
        sweep.fail = True
        room.record(sweep, "hunter", HUNTER)
        self.assertEqual(room.take(), Reading(150.0, 800.0))

    def test_a_reading_goes_stale_when_the_guard_stops_measuring(self):
        room, sweep = room_with([400.0] * len(DIRECTIONS))
        for _ in range(MAX_AGE):
            self.assertIsNotNone(room.take())
        self.assertIsNone(room.take())
        sweep.fail = True
        room.record(sweep, "hunter", HUNTER)
        self.assertIsNone(room.take())
        sweep.fail = False
        room.record(sweep, "hunter", HUNTER)
        self.assertIsNotNone(room.take())

    def test_clear_forgets_everything(self):
        room, _sweep = room_with([400.0] * len(DIRECTIONS))
        room.clear()
        self.assertIsNone(room.take())
        self.assertEqual(room.next, 0)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
