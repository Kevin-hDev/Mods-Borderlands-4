"""Which Vault Hunter companion the player aims at (decision 53 of docs/renforts/README.md): the game names all six
« Lemmy » on the bar it shows for the target aimed at, and that page has nothing that tells them apart. It Follows
works it out and the bars' service hands it to that page (bars_service.py), which shows that name instead.

The one aimed at is the nearest along the camera's line whose place is within REACH_CM of it: a body is about 180 cm
tall, its place at its middle. Kept HOLD_S after the line leaves it, as the game keeps its bar a moment; another one
aimed at replaces it at once. The allies are left out: the game gives them their own names. The camera is read as
Benefix Ohm Attack and Apex Grapple read it (GetCameraLocation, GetCameraRotation, verified in game); a read that
fails names no one, said once.
"""

import math
from typing import Any, Callable

from .. import reads, report
from . import hunters

REACH_CM = 80.0
FARTHEST_CM = 15000.0
HOLD_S = 1.0
MAX_TEXT = 120

Spot = tuple[float, float, float]


def facing(rotation: Any) -> Spot:
    """The unit direction of a rotation's pitch and yaw, in degrees; its roll changes nothing."""
    pitch, yaw = math.radians(float(rotation.Pitch)), math.radians(float(rotation.Yaw))
    return math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch)


def nearest(eye: Spot, ahead: Spot, spots: list[tuple[str, Spot]]) -> str | None:
    """The name of the nearest place in front of `eye`, along `ahead`, within REACH_CM of that line and FARTHEST_CM
    of the eye; None when there is none."""
    best: tuple[float, str] | None = None
    for name, spot in spots:
        towards = tuple(spot[axis] - eye[axis] for axis in range(3))
        along = sum(towards[axis] * ahead[axis] for axis in range(3))
        if along <= 0.0 or along > FARTHEST_CM:
            continue
        off = math.sqrt(max(0.0, sum(part * part for part in towards) - along * along))
        if off <= REACH_CM and (best is None or along < best[0]):
            best = (along, name)
    return None if best is None else best[1]


def camera(pc: Any) -> tuple[Spot, Spot]:
    manager = pc.PlayerCameraManager
    where = manager.GetCameraLocation()
    return (float(where.X), float(where.Y), float(where.Z)), facing(manager.GetCameraRotation())


class Aimed:
    """The hunter aimed at, for one team: clock() the team's time."""

    def __init__(self, clock: Callable[[], float]) -> None:
        self.clock = clock
        self.name: str | None = None
        self.until = 0.0
        self.failed = False

    def look(self, pc: Any, follows: list, names: dict) -> str | None:
        """The name shown of the hunter aimed at now, or the last one for HOLD_S; None otherwise."""
        now = self.clock()
        seen = self._seen(pc, follows, names)
        if seen is not None:
            self.name, self.until = seen, now + HOLD_S
        elif self.name is not None and now >= self.until:
            self.name = None
        return self.name

    def _seen(self, pc: Any, follows: list, names: dict) -> str | None:
        if pc is None:
            return None
        try:
            eye, ahead = camera(pc)
        except Exception as error:
            if not self.failed:
                self.failed = True
                report.note("companion_aim_failed", why=f"{type(error).__name__}:{str(error)[:MAX_TEXT]}")
            return None
        spots = []
        for one in follows:
            if one.companion not in hunters.BY_NAME:
                continue
            spot = reads.point(one.actor())
            if spot is not None:
                spots.append((names.get(one.companion, one.companion), spot))
        return nearest(eye, ahead, spots)
