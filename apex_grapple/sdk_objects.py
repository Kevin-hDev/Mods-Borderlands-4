"""Test doubles for characters, traces, and animation assets."""

import types
from typing import Any


def vector(x: float, y: float, z: float = 0.0) -> Any:
    return types.SimpleNamespace(X=x, Y=y, Z=z)


def event(name: str) -> Any:
    return types.SimpleNamespace(name=name)


class Mode:
    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f"<EMovementMode.{self.name}: 1>"


def mapping(action: str, key: str) -> Any:
    return types.SimpleNamespace(Action=types.SimpleNamespace(Name=action), Key=types.SimpleNamespace(KeyName=key))


class FakeMovement:
    def __init__(self) -> None:
        self.MovementMode = Mode("MOVE_Walking")
        self.Velocity = vector(0.0, 0.0, 0.0)
        self.GravityScale = 1.0
        # Measured native mantle state: -1 idle, nonnegative throughout a mantle.
        self.ReplicatedMantleState = types.SimpleNamespace(ActionIndex=-1)
        # The game's own gravity, measured on 2026-09-20. Negative, as Unreal answers it.
        self.gravity_z = -980.0
        self.modes: list[int] = []

    def GetGravityZ(self) -> float:
        return self.gravity_z * self.GravityScale

    def SetMovementMode(self, mode: int, custom: int) -> None:
        self.modes.append(mode)
        self.MovementMode = Mode("MOVE_Falling" if mode == 3 else "MOVE_Walking")


class FakeComponent:
    """A scene component as the rope probe reads one: a name, a class, maybe an asset and children.

    Only the fields a test hands it exist on it, on purpose: half the probe's job is to say which
    fields this build of the game really carries, and a fake that answers everything hides that.
    """

    def __init__(self, name: str, class_name: str = "SceneComponent", asset: str | None = None,
                 children: list | None = None, **fields: Any) -> None:
        self.Name = name
        self.Class = types.SimpleNamespace(Name=class_name)
        if asset is not None:
            self.Asset = types.SimpleNamespace(Name=asset,
                                               Class=types.SimpleNamespace(Name="NiagaraSystem"))
        self.AttachChildren = children if children is not None else []
        # A lever whose name carries none of the seven words the probe used to filter on, kept so a
        # test can prove the filter is gone.
        self.SetAllowScalability = lambda allowed: None
        for key, value in fields.items():
            setattr(self, key, value)


class FakeCharacter:
    def __init__(self) -> None:
        self.RootComponent = None
        self.CharacterMovement = FakeMovement()
        self.anim = object()
        self.Mesh = types.SimpleNamespace(GetAnimInstance=lambda: self.anim)
        self.location = vector(0.0, 0.0, 100.0)
        self.input = vector(0.0, 0.0, 0.0)
        self.pitch, self.yaw = 0.0, 0.0
        self.Controller = types.SimpleNamespace(
            GetControlRotation=lambda: types.SimpleNamespace(Pitch=self.pitch, Yaw=self.yaw, Roll=0.0))

    def K2_GetActorLocation(self) -> Any:
        return self.location

    def GetLastMovementInputVector(self) -> Any:
        return self.input


class FakeKismet:
    """Trace answers distance, class, and optionally the actor instance name."""

    def __init__(self) -> None:
        self.hit: tuple[float, str] | tuple[float, str, str] | None = None
        self.calls: list[tuple] = []

    def LineTraceSingle(self, context: Any, start: Any, end: Any, channel: int, complex_trace: bool, ignored: list,
                        draw: int, out: Any, ignore_self: bool, colour: Any, hit_colour: Any,
                        draw_time: float) -> Any:
        self.calls.append((start, end, channel))
        if self.hit is None:
            return False, [], types.SimpleNamespace()
        distance, name, *instance = self.hit
        actor = None if not name else types.SimpleNamespace(
            Class=types.SimpleNamespace(Name=name), Name=instance[0] if instance else name)
        return True, [], types.SimpleNamespace(Distance=distance, Actor=actor)


class FakePoint:
    """One of the game's own grapple points, as find_all hands them over."""

    def __init__(self, x: float, y: float, z: float) -> None:
        self.spot = vector(x, y, z)

    def K2_GetActorLocation(self) -> Any:
        return self.spot


class FakeSequence:
    """An animation asset, as AS_Grapple comes back."""

    def __init__(self, length: float = 0.8) -> None:
        self.length = length

    def GetPlayLength(self) -> float:
        return self.length


class FakeArms:
    """The first-person arms' animation instance, and what was played on it."""

    def __init__(self, character: Any) -> None:
        self.played: list[dict] = []
        self.stopped: list[tuple] = []
        self.montages: list[Any] = []
        self.active_montage = None
        self.raises = False
        mesh = types.SimpleNamespace(Name="FirstPersonArms", Outer=character)
        mesh.GetAnimInstance = lambda: self
        self.Outer = mesh

    def PlaySlotAnimationAsDynamicMontage(self, **kwargs: Any) -> Any:
        if self.raises:
            raise RuntimeError("the arms are gone")
        self.played.append(kwargs)
        montage = types.SimpleNamespace(slot=kwargs["SlotNodeName"])
        self.montages.append(montage)
        self.active_montage = montage
        return montage

    def Montage_Stop(self, blend: float, montage: Any) -> None:
        self.stopped.append((blend, montage.slot))
        if self.active_montage is montage:
            self.active_montage = None

    def StopSlotAnimation(self, blend: float, slot: str) -> None:
        self.stopped.append((blend, slot))


def player(character: Any, mappings: list) -> Any:
    return types.SimpleNamespace(
        OakCharacter=character,
        PlayerInput=types.SimpleNamespace(EnhancedActionMappings=mappings),
        # None on purpose: game.aim then falls back to the eyes, the path every test walks unless it
        # sets a camera of its own.
        PlayerCameraManager=None,
    )
