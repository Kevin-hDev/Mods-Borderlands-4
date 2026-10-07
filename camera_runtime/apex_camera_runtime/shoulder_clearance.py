"""How much of the shoulder's room each side keeps free, read during the camera's wall check.

The wall check sweeps the native camera (anchor) to the camera with our offset (desired): its free share is the shown
side's room. The other side mirrors that offset across the camera's right axis. Sweeping it costs a second trace, so it
runs only when the shoulder state asks (a swap may happen and the shown side is cramped, or a swap is under way).
The cameras' positions are kept for the view ahead (shoulder_sight.py), measured on the game's tick.
"""

import math
from typing import NamedTuple

# Below this sideways offset (cm), mid-switch, the two sides are the same point: no reading.
MIN_SIDE = 10.0
# Readings older than this many camera ticks are stale: the wall check stopped running.
MAX_AGE = 3


class Reading(NamedTuple):
    room: float
    other_room: float | None
    camera: tuple
    # Where the other side's camera would stand, as far as its room lets it; None when not measured.
    other_camera: tuple | None


class ShoulderClearance:
    def __init__(self) -> None:
        # Set by the shoulder state each tick.
        self.wanted = False
        self.clear()

    def clear(self) -> None:
        self.reading: Reading | None = None
        self.age = MAX_AGE

    def record(self, sweep, actor, manager, anchor, desired, distance: float, blocked: bool, position) -> None:
        length = math.dist(anchor, desired)
        room = 0.0 if blocked else distance / length
        self.reading, self.age = Reading(room, None, tuple(position), None), 0
        if not self.wanted:
            return
        yaw = math.radians(float(manager.GetCameraRotation().Yaw))
        right = (-math.sin(yaw), math.cos(yaw), 0.0)
        side = sum((b - a) * r for a, b, r in zip(anchor, desired, right))
        if abs(side) < MIN_SIDE:
            return
        mirrored = tuple(d - 2.0 * side * r for d, r in zip(desired, right))
        # The resolver reads the shown side's reduced-volume flag after this frame's sweep; keep it.
        reduced = sweep.reduced
        try:
            other_room = sweep.distance(actor, anchor, mirrored) / math.dist(anchor, mirrored)
        finally:
            sweep.reduced = reduced
        other_camera = tuple(a + (m - a) * other_room for a, m in zip(anchor, mirrored))
        self.reading = Reading(room, other_room, tuple(position), other_camera)

    def take(self) -> Reading | None:
        if self.age >= MAX_AGE:
            return None
        self.age += 1
        return self.reading
