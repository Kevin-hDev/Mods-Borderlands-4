"""How much of the shoulder's room each side keeps free, read during the camera guard's frame.

The guard sweeps from the hunter's line (anchor) to the shoulder the game was given (desired): its free share is the
shown side's room. The other side mirrors that offset across the camera's right axis. Sweeping it costs a second trace, so it
runs only when the shoulder state asks (a swap may happen and the shown side is cramped, or a swap is under way).
The cameras' positions are kept for the view ahead (shoulder_sight.py), measured on the game's tick.

A pole behind the hunter, between the game's camera and the shoulder, cut that sweep and swapped the shoulder (Kevin,
2026-10-08, docs/third_person_fov/camera/releves/2026-10-08-epaule-pont/sdk-essai-2-mesures.log). So while the
automatic shoulder is on, a cramped side is swept again a little ahead and a little behind, and keeps the roomiest of
the three: a pole cuts one sweep, a wall alongside all three. The camera itself still stops at the pole (the game's
collision).
"""

import math
from typing import NamedTuple

from .shoulder_auto import CLEAR
from .shoulder_sight import seen

# Below this sideways offset (cm), mid-switch, the two sides are the same point: no reading.
MIN_SIDE = 10.0
# Readings older than this many camera ticks are stale: the guard stopped measuring.
MAX_AGE = 3
# How far ahead and behind the extra sweeps run (cm): more than a pole's width, less than a wall's.
SPREAD_CM = 50.0


class Reading(NamedTuple):
    room: float
    other_room: float | None
    camera: tuple
    # Where the other side's camera would stand, as far as its room lets it; None when not measured.
    other_camera: tuple | None
    # What cut each side's roomiest sweep, for the swap's log line (shoulder_sight.seen).
    seen: str = ""
    other_seen: str = ""


def _met(sweep, distance: float, length: float) -> str:
    hit = getattr(sweep, "hit", None)
    if hit is not None:
        return seen(hit, distance)
    return "clear" if distance >= length else f"{distance:.0f} cm"


class ShoulderClearance:
    def __init__(self) -> None:
        # Set by the shoulder state each tick: the other side is wanted; the automatic shoulder is on.
        self.wanted = False
        self.active = False
        self.clear()

    def clear(self) -> None:
        self.reading: Reading | None = None
        self.age = MAX_AGE

    def record(self, sweep, actor, manager, anchor, desired, distance: float, position) -> None:
        length = math.dist(anchor, desired)
        room = distance / length
        self.reading, self.age = Reading(room, None, tuple(position), None), 0
        if not (self.wanted or self.active):
            return
        yaw = math.radians(float(manager.GetCameraRotation().Yaw))
        right = (-math.sin(yaw), math.cos(yaw), 0.0)
        forward = (math.cos(yaw), math.sin(yaw), 0.0)
        side = sum((b - a) * r for a, b, r in zip(anchor, desired, right))
        if abs(side) < MIN_SIDE:
            return
        # The guard's own sweep has just run: its contact is the shown side's.
        room, met = self._widest(sweep, actor, anchor, desired, forward, room, _met(sweep, distance, length))
        self.reading = Reading(room, None, tuple(position), None, met)
        if not self.wanted:
            return
        mirrored = tuple(d - 2.0 * side * r for d, r in zip(desired, right))
        other_length = math.dist(anchor, mirrored)
        other_distance = sweep.distance(actor, anchor, mirrored)
        other_room = other_distance / other_length
        # The other camera stands where its own sweep stops; the extra sweeps only judge the room.
        other_camera = tuple(a + (m - a) * other_room for a, m in zip(anchor, mirrored))
        other_room, other_met = self._widest(sweep, actor, anchor, mirrored, forward, other_room,
                                             _met(sweep, other_distance, other_length))
        self.reading = Reading(room, other_room, tuple(position), other_camera, met, other_met)

    def _widest(self, sweep, actor, anchor, end, forward, room: float, met: str) -> tuple:
        """The roomiest of the sweep and the same sweep moved ahead and behind, once the side is cramped, with what
        cut it."""
        if not self.active or room >= CLEAR:
            return room, met
        length = math.dist(anchor, end)
        for shift in (SPREAD_CM, -SPREAD_CM):
            moved = [tuple(p + shift * f for p, f in zip(point, forward)) for point in (anchor, end)]
            try:
                distance = sweep.distance(actor, *moved)
            except ValueError:
                # Moved, the sweep can start inside the pole or wall: it proves nothing, and must never stop the wall
                # check that places the camera (2026-10-08 third trial: twice "Camera collision unavailable").
                continue
            if distance / length > room:
                room, met = distance / length, _met(sweep, distance, length)
            if room >= CLEAR:
                break
        return room, met

    def take(self) -> Reading | None:
        if self.age >= MAX_AGE:
            return None
        self.age += 1
        return self.reading
