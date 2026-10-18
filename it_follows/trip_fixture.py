"""A fake game for a trip to a starting point (start_trip.py, start_cover.py): the player's controller with its camera,
its keys and its turn; the character with its place, its moves, its shield and its world; the ground under a point,
which a test sets as the place loads; a clock the test moves; the frame hook run as the game would run it."""

import math
from types import SimpleNamespace
from typing import Any

FRAME = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"


class Clock:
    now = 100.0

    def __call__(self) -> float:
        return self.now


class Camera:
    def __init__(self, game: "Game") -> None:
        self.game = game

    def StartCameraFade(self, FromAlpha, ToAlpha, Duration, Color, bShouldFadeAudio, bHoldWhenFinished):
        if self.game.refuse.get("fade"):
            raise RuntimeError("fade refused")
        self.game.camera.append(("fade", FromAlpha, ToAlpha, Duration, bHoldWhenFinished))

    def StopCameraFade(self):
        self.game.camera.append(("stop",))


class Controller:
    def __init__(self, game: "Game") -> None:
        self.game, self.PlayerCameraManager, self.ignored = game, Camera(game), True
        self.turns: list[float] = []
        self.OakCharacter: Any = None

    def IsMoveInputIgnored(self) -> bool:
        return self.ignored

    def SetControlRotation(self, rotation: Any, bResetCamera: bool) -> None:
        if self.game.refuse.get("turn"):
            raise RuntimeError("turn refused")
        self.turns.append((rotation.Yaw, bResetCamera))


class Character:
    def __init__(self, game: "Game", at: tuple, world: str = "World_P") -> None:
        self.game, self.at, self._damageable = game, at, True
        self.Outer = SimpleNamespace(Outer=SimpleNamespace(Name=world))
        self.CharacterMovement = SimpleNamespace(Velocity=None)
        self.CapsuleComponent = SimpleNamespace(GetScaledCapsuleHalfHeight=lambda: 90.0)
        self.moves: list[tuple] = []

    @property
    def bCanBeDamaged(self) -> bool:
        return self._damageable

    @bCanBeDamaged.setter
    def bCanBeDamaged(self, value: bool) -> None:
        self._damageable = value

    def K2_GetActorLocation(self) -> Any:
        return SimpleNamespace(X=self.at[0], Y=self.at[1], Z=self.at[2])

    def K2_GetActorRotation(self) -> Any:
        return SimpleNamespace(Pitch=0.0, Yaw=10.0, Roll=0.0)

    def K2_TeleportTo(self, DestLocation: Any, DestRotation: Any) -> Any:
        if self.game.refuse.get("broken"):
            raise RuntimeError("move broken")
        if self.game.refuse.get("move"):
            return False
        self.at = (DestLocation.X, DestLocation.Y, DestLocation.Z)
        self.moves.append(self.at)
        self.game.lines_before_move.append(len(self.game.log))
        return True


class Library:
    """KismetSystemLibrary's trace: what it meets at the game's floor height, or nothing."""

    def __init__(self, game: "Game") -> None:
        self.game = game

    def LineTraceSingle(self, _world, start, end, _channel, _complex, _ignored, _draw, _hit, _self, _colour,
                        _hit_colour, _time):
        if self.game.refuse.get("trace"):
            raise RuntimeError("trace refused")
        self.game.traces.append((start.Z, end.Z))
        floor = self.game.floor
        if floor is None or not end.Z <= floor <= start.Z:
            return False, None, SimpleNamespace(ImpactPoint=SimpleNamespace(Z=math.nan))
        return True, None, SimpleNamespace(ImpactPoint=SimpleNamespace(Z=floor), Component=None, PhysMaterial=None)


class Game:
    """The fake game: install(state) registers its trace library, its controller and the log it reads; run(state) runs
    the frame hooks once. refuse names what the game refuses: fade, turn, move (answered False), broken (a move that
    raises), trace."""

    def __init__(self, at: tuple = (1000.0, 2000.0, 300.0), world: str = "World_P") -> None:
        self.camera: list[tuple] = []
        self.traces: list[tuple] = []
        self.refuse: dict[str, bool] = {}
        self.floor: float | None = None
        # The log's lines, and how many it held at each move: each call is written before it is made.
        self.log: list[str] = []
        self.lines_before_move: list[int] = []
        self.pc = Controller(self)
        self.character = Character(self, at, world)
        self.pc.OakCharacter = self.character

    def install(self, state: dict) -> None:
        state["classes"]["KismetSystemLibrary"] = SimpleNamespace(ClassDefaultObject=Library(self))
        state["pc"] = self.pc
        self.log = state["info"]

    @staticmethod
    def run(state: dict) -> None:
        for hook in list(state["hooks"].values()):
            hook.fn(None, None, None, None)
