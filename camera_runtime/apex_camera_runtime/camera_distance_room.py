"""The room around the hunter for the automatic camera distance (camera_distance_auto.py), read in the camera guard's
frame (camera_guard.py), one direction per frame so a frame never costs more than one sweep.

The sweeps start at the camera's pivot, the hunter's head. Upward gives the ceiling. Around, the four lines through
the hunter (the world's axes and its diagonals) each give a passage's width: the narrowest one does not depend on where
the camera looks, so turning the camera in a corridor never changes the distance (Kevin, 2026-10-11,
docs/third_person_fov/camera/2026-10-07-idees-troisieme-personne.md, list 2 n° 2).
"""

import math
from typing import NamedTuple

# The camera's pivot above the hunter's centre (cm): the game's camera folded onto it stood 71 cm above the centre on
# all six entries measured (collision_config.py, FOLD_REACH_CM).
HEAD_CM = 71.0
# How far each sweep looks (cm), past the far camera's 360 cm: beyond it the side counts as open.
REACH_CM = 400.0
AROUND = tuple((math.cos(math.radians(angle)), math.sin(math.radians(angle)), 0.0) for angle in range(0, 360, 45))
DIRECTIONS = ((0.0, 0.0, 1.0),) + AROUND
# Readings older than this many camera frames are stale: the guard stopped measuring.
MAX_AGE = 3


class Reading(NamedTuple):
    # Free height above the pivot (cm).
    ceiling: float
    # The narrowest passage's width through the pivot (cm).
    narrowest: float


class CameraDistanceRoom:
    def __init__(self) -> None:
        self.clear()

    def clear(self) -> None:
        self.free: list = [None] * len(DIRECTIONS)
        self.next = 0
        self.age = MAX_AGE

    def record(self, sweep, actor, hunter: tuple) -> None:
        """Sweep the next direction from the pivot."""
        index = self.next
        self.next = (index + 1) % len(DIRECTIONS)
        head = (hunter[0], hunter[1], hunter[2] + HEAD_CM)
        end = tuple(h + REACH_CM * d for h, d in zip(head, DIRECTIONS[index]))
        try:
            self.free[index] = sweep.distance(actor, head, end)
        except ValueError:
            # A sweep starting inside a wall proves nothing: that direction keeps its last width until the next round.
            return
        self.age = 0

    def take(self) -> Reading | None:
        """The room once every direction has been swept, None while stale."""
        if self.age >= MAX_AGE or None in self.free:
            return None
        self.age += 1
        around = self.free[1:]
        half = len(around) // 2
        return Reading(self.free[0], min(around[i] + around[i + half] for i in range(half)))
