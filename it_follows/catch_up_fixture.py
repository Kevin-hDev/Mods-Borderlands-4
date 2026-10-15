"""Fakes of the catch-up's world, shared by test_ground.py and test_catch_up.py: the game's trace library, an enemy
with its capsule and its teleport, and structures that keep the name of their type. Used after sdk_stubs.install()."""

import math
import sys
import types
from typing import Any

LANDSCAPE = "/Game/World.Landscape_1.LandscapeHeightfieldCollisionComponent_7"


def keep_struct_names() -> None:
    """unrealsdk.make_struct then gives each structure its type's name as struct_name, so that a test reads it."""
    sys.modules["unrealsdk"].make_struct = lambda name, **fields: types.SimpleNamespace(struct_name=name, **fields)


class Named:
    """What a trace met, known by its full name."""

    def __init__(self, path: str) -> None:
        self.path = path

    def _path_name(self) -> str:
        return self.path


class TraceLibrary:
    """The trace library's default object: meets the ground at ground_z between the trace's two ends unless told
    otherwise (a ground_z that is no number is met wherever the trace goes); keeps what it was asked and notes each
    trace in events. raises: the error each trace raises."""

    def __init__(self, events: list, ground_z: float | None = 40.0) -> None:
        self.events, self.ground_z = events, ground_z
        self.asked: list[tuple] = []
        self.raises: Exception | None = None
        self.component: Any = Named(LANDSCAPE)
        self.material: Any = None

    def LineTraceSingle(self, *args: Any) -> tuple:
        self.asked.append(args)
        self.events.append(("trace",))
        if self.raises is not None:
            raise self.raises
        start, end, ground_z = args[1], args[2], self.ground_z
        met = ground_z is not None and (math.isnan(ground_z) or end.Z <= ground_z <= start.Z)
        result = types.SimpleNamespace(ImpactPoint=types.SimpleNamespace(Z=ground_z if met else 0.0),
                                       Component=self.component, PhysMaterial=self.material)
        return met, args[5], result


class Enemy:
    """An enemy: its capsule's half height, half (an Exception raises when read), read reads times; its teleport
    answers answer (an Exception raises), notes itself in events and keeps where the enemy went and the structures
    it was given."""

    def __init__(self, name: str = "cat", half: Any = 60.0, answer: Any = True, events: list | None = None) -> None:
        self.name, self.half, self.answer = name, half, answer
        self.events = events if events is not None else []
        self.reads = 0
        self.went: tuple | None = None
        self.given: tuple | None = None
        self.CapsuleComponent = types.SimpleNamespace(GetScaledCapsuleHalfHeight=self._half_height)

    def _half_height(self) -> float:
        self.reads += 1
        if isinstance(self.half, Exception):
            raise self.half
        return self.half

    def K2_TeleportTo(self, *, DestLocation: Any, DestRotation: Any) -> Any:
        self.events.append(("teleport", self.name))
        if isinstance(self.answer, Exception):
            raise self.answer
        self.given = (DestLocation, DestRotation)
        self.went = (DestLocation.X, DestLocation.Y, DestLocation.Z, DestRotation.Yaw)
        return self.answer
