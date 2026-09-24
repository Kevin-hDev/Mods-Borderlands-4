"""Player, movement, animation and trace fakes for Apex Movement tests."""

import types
from typing import Any

from sdk_stubs_assets import jump_goals
from sdk_stubs_core import Mode, vector

class FakeMovement:
    def __init__(self) -> None:
        self.MovementMode = Mode("MOVE_Walking")
        self.MinAnalogWalkSpeed = 0.0
        self.bWantsToSprint = False
        self.bWantsToStartSprinting = False
        self.bIsSprinting = False
        self.Velocity = vector(0.0, 0.0)
        self.MaxGroundSpeedScale = types.SimpleNamespace(Value=1.15)
        self.ControlledMoveReplicationData = types.SimpleNamespace(ControlledMove=None, PackedDirection=vector(0.0, 0.0))
        self.CurrentFloor = types.SimpleNamespace(HitResult=types.SimpleNamespace(ImpactNormal=vector(0.0, 0.0, 1.0)))
        self.GravityScale, self.MaxAcceleration, self.AirControl = 1.0, 2048.0, 0.6
        # Glide attributes, with the game's values read on 2026-09-20: a pair whose Value the game computes from
        # its BaseValue, as the vehicle attributes do.
        self.GlidingSpeed = types.SimpleNamespace(BaseValue=1200.0, Value=1200.0)
        self.GlidingAcceleration = types.SimpleNamespace(BaseValue=400.0, Value=400.0)
        self.ReplicatedMantleState = types.SimpleNamespace(ActionIndex=-1)
        self.mantle_allowed = False
        # What the game answers when asked whether it performs a controlled move; the copy above can say otherwise.
        self.performing = False
        self.LadderState = types.SimpleNamespace(OverlappingClimbables=[])
        self.goals = jump_goals()
        self.type_sets: list[str] = []
        self.CurrentJump = types.SimpleNamespace(
            JumpType=types.SimpleNamespace(TagName="Movement.JumpType.DefaultJump"), JumpGoal=self.goals["DefaultJump"],
        )

    def CanStartPassiveMantle(self) -> bool:
        return self.mantle_allowed

    def IsPerformingControlledMove(self) -> bool:
        return self.performing

    def SetCurrentJumpType(self, tag: Any) -> None:
        self.type_sets.append(tag.TagName)
        short = tag.TagName.rsplit(".", 1)[-1]
        self.CurrentJump = types.SimpleNamespace(JumpType=tag, JumpGoal=self.goals.get(short))


class FakeCharacter:
    def __init__(self) -> None:
        self.CharacterMovement = FakeMovement()
        self.anim = object()
        self.Mesh = types.SimpleNamespace(GetAnimInstance=lambda: self.anim)
        self.ZoomState = types.SimpleNamespace(bWantsToZoom=False, State=types.SimpleNamespace(name="NotZoomed"))
        self.bIsCrouched = False
        self.input = vector(0.0, 0.0)
        self.Controller = types.SimpleNamespace(GetControlRotation=lambda: types.SimpleNamespace(Yaw=self.yaw))
        self.yaw = 0.0
        self.calls: list[tuple] = []
        self.slam_result = True
        self.JumpCurrentCount = 0
        self.bPressedJump = False
        self.location = vector(0.0, 0.0, 100.0)
        self.CapsuleComponent = types.SimpleNamespace(GetScaledCapsuleHalfHeight=lambda: 93.0)

    def SetWantsToDash(self, wanted: bool, direction: int) -> None:
        self.calls.append(("SetWantsToDash", wanted, direction))

    def SetWantsToSlide(self, wanted: bool) -> None:
        self.calls.append(("SetWantsToSlide", wanted))

    def AttemptGroundSlam(self) -> bool:
        self.calls.append(("AttemptGroundSlam",))
        return self.slam_result

    def GetLastMovementInputVector(self) -> Any:
        return self.input

    def K2_GetActorLocation(self) -> Any:
        return self.location


class FakeSequence:
    def __init__(self, length: float) -> None:
        self.length = length

    def GetPlayLength(self) -> float:
        return self.length


class FakeArms:
    """The first-person arms' animation instance: records the montages played and the slots stopped."""

    def __init__(self) -> None:
        self.plays: list[dict] = []
        self.stops: list[tuple] = []
        self.Outer: Any = None

    def PlaySlotAnimationAsDynamicMontage(self, **kwargs: Any) -> Any:
        self.plays.append(kwargs)
        return object()

    def StopSlotAnimation(self, blend_out: float, slot: str) -> None:
        self.stops.append((blend_out, slot))


def add_arms(state: dict, character: Any, mesh_name: str = "FirstPersonArms") -> FakeArms:
    """Puts an animation instance among those find_all returns, on a mesh of that name belonging to the character."""
    arms = FakeArms()
    arms.Outer = types.SimpleNamespace(Name=mesh_name, Outer=character, GetAnimInstance=lambda: arms)
    state["anim_instances"].append(arms)
    return arms


class FakeKismet:
    """KismetSystemLibrary's class default object: every trace hits `hit`, a (distance, normal) pair, when it is set.

    `hits_by_z` answers per height instead, keyed by the rounded Z of the trace's start, for the heights a real
    structure lets through.
    """

    def __init__(self) -> None:
        self.hit: tuple[float, Any] | None = None
        self.hits_by_z: dict[int, tuple[float, Any] | None] | None = None
        self.calls: list[tuple] = []

    def LineTraceSingle(self, context: Any, start: Any, end: Any, channel: int, complex_trace: bool, ignored: list,
                        draw: int, out: Any, ignore_self: bool, colour: Any, hit_colour: Any, draw_time: float) -> Any:
        self.calls.append((start, end, channel, ignore_self))
        hit = self.hit if self.hits_by_z is None else self.hits_by_z.get(round(start.Z))
        if hit is None:
            return False, [], types.SimpleNamespace()
        distance, normal = hit
        return True, [], types.SimpleNamespace(Distance=distance, Normal=normal)
