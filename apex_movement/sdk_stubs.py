"""Fake SDK modules so Apex Movement's logic can be tested outside the game.

Installed into sys.modules before importing apex_movement.
"""

import copy
import enum
import sys
import types
from typing import Any

SLIDE_PATH = "/Game/PlayerCharacters/_Shared/Tricks/ControlledMoves/Move_Slide.Move_Slide"
DASH_PATH = "/Game/PlayerCharacters/_Shared/Tricks/ControlledMoves/Move_Dash.Move_Dash"
CLIMB_ANIMATION_PATH = "/Game/PlayerCharacters/_Shared/Animation/1st/SharedSkills/AS_Wall_Climb_U.AS_Wall_Climb_U"


class FakeOption:
    def __init__(self, identifier: str, value: Any, *args: Any, **kwargs: Any) -> None:
        self.on_change_anytime = None
        # args holds a slider's bounds, in mods_base's order: min_value, max_value.
        self.identifier, self.value, self.args, self.kwargs = identifier, value, args, kwargs
        self.display_name = kwargs.get("display_name", identifier)

    def __setattr__(self, name: str, value: Any) -> None:
        # Like mods_base: the change callback runs before a new value is stored, loading a settings file included.
        if name == "value" and getattr(self, "on_change_anytime", None) is not None:
            self.on_change_anytime(self, value)
        super().__setattr__(name, value)


class FakeNested:
    def __init__(self, identifier: str, children: list, **kwargs: Any) -> None:
        self.identifier, self.children, self.kwargs = identifier, children, kwargs
        self.display_name = kwargs.get("display_name", identifier)


class FakeHook:
    def __init__(self, fn: Any, path: str, identifier: str) -> None:
        self.fn, self.path, self.identifier, self.enabled = fn, path, identifier, False

    def __call__(self, *args: Any) -> Any:
        return self.fn(*args)

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False


class FakeMod:
    """Behaves as mods_base.Mod does wherever the mod depends on it, down to the order of each step (mod.py:260-308).

    The fake used to skip the settings file, so no test ever saw a mod enabled from it while build_mod was still
    running — which is how a guard calling the module's own `mod` from on_enable shipped (review, 2026-09-18).
    """

    def __init__(self, state: dict, **kwargs: Any) -> None:
        self.state, self.kwargs, self.is_enabled = state, kwargs, False
        self.settings_file = types.SimpleNamespace(exists=lambda: state["settings_exists"])
        # What the settings file holds for "enabled" after the mod's last save; None while it never saved.
        self.saved_enabled: bool | None = None

    def enable(self) -> None:
        if self.is_enabled:
            return
        self.is_enabled = True
        for hook in self.kwargs.get("hooks") or []:
            hook.enable()
        if self.kwargs.get("on_enable"):
            self.kwargs["on_enable"]()
        self.saved_enabled = self.is_enabled

    def disable(self) -> None:
        if not self.is_enabled:
            return
        self.is_enabled = False
        for hook in self.kwargs.get("hooks") or []:
            hook.disable()
        if self.kwargs.get("on_disable"):
            self.kwargs["on_disable"]()
        self.saved_enabled = False


def vector(x: float, y: float, z: float = 0.0) -> Any:
    return types.SimpleNamespace(X=x, Y=y, Z=z)


class Mode:
    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f"<EMovementMode.{self.name}: 1>"


class Direction(enum.Enum):
    """Stands for the game's ERelativeDirectionType, with the values read in game."""

    Default = 0
    ParentVelocity2D = 5
    ParentAimDirection2D = 18


class FakeSlideAsset:
    """Move_Slide with its game values; its structs come back as copies, as the SDK may hand them out."""

    def __init__(self) -> None:
        self._speed = types.SimpleNamespace(constant=720.0)
        self._launch = types.SimpleNamespace(RelativeDirection=Direction.ParentAimDirection2D)
        self._steering = types.SimpleNamespace(constant=55.0)
        self._duration = types.SimpleNamespace(constant=1.35)
        self.bSpeedAffectedByMaxGroundSpeedScale = True
        self.bUseSlopeCurve = True
        # The curve read in game on 2026-09-16; its points are live views, as SDK arrays of structs are.
        self.SpeedScaleCurve = types.SimpleNamespace(EditorCurveData=types.SimpleNamespace(keys=[
            curve_key(0.0, 1.1017, 0.0, -0.2), curve_key(0.5675, 0.9728, -0.3, -0.3), curve_key(0.7437, 0.7737, -1.4, -1.4),
            curve_key(1.0, 0.3722, -2.0, 0.0),
        ]))
        self.SpeedSlopeScaleCurve = types.SimpleNamespace(EditorCurveData=types.SimpleNamespace(keys=[
            curve_key(-1.0, 0.5, 0.0, 0.5), curve_key(0.0, 1.0, 0.5, 1.4), curve_key(0.7, 2.0, 0.0, 0.0),
            curve_key(1.0, 2.0, 0.0, 0.0),
        ]))

    @property
    def speed(self) -> Any:
        return copy.copy(self._speed)

    @speed.setter
    def speed(self, value: Any) -> None:
        self._speed = copy.copy(value)

    @property
    def LaunchDirection(self) -> Any:
        return copy.copy(self._launch)

    @LaunchDirection.setter
    def LaunchDirection(self, value: Any) -> None:
        self._launch = copy.copy(value)

    @property
    def Duration(self) -> Any:
        return copy.copy(self._duration)

    @Duration.setter
    def Duration(self, value: Any) -> None:
        self._duration = copy.copy(value)

    @property
    def MoveLRRate(self) -> Any:
        return copy.copy(self._steering)

    @MoveLRRate.setter
    def MoveLRRate(self, value: Any) -> None:
        self._steering = copy.copy(value)


def curve_key(time: float, value: float, arrive: float = 0.0, leave: float = 0.0) -> Any:
    return types.SimpleNamespace(time=time, Value=value, ArriveTangent=arrive, LeaveTangent=leave)


class FakeDashAsset:
    """Move_Dash with the values read in game on 2026-09-16: Duration comes back as a copy, as the SDK may hand structs
    out; the curve points are live views, as SDK arrays of structs are, unless copy_keys makes them copies."""

    def __init__(self, copy_keys: bool = False) -> None:
        self._duration = types.SimpleNamespace(constant=0.33)
        self.speed = types.SimpleNamespace(constant=2500.0)
        self.copy_keys = copy_keys
        self._keys = [curve_key(0.0, 1.0), curve_key(0.15, 1.0, 0.0, -2.0), curve_key(0.17, 0.181, -2.0, 1.5),
                      curve_key(0.33, 0.48, 1.5, 0.0)]

    @property
    def Duration(self) -> Any:
        return copy.copy(self._duration)

    @Duration.setter
    def Duration(self, value: Any) -> None:
        self._duration = copy.copy(value)

    @property
    def SpeedScaleCurve(self) -> Any:
        keys = [copy.copy(key) for key in self._keys] if self.copy_keys else self._keys
        return types.SimpleNamespace(EditorCurveData=types.SimpleNamespace(keys=keys))


class FakeKeybind:
    """Stands in for mods_base.keybind: the tests fire key events by calling state["keybinds"][key]."""

    def __init__(self, state: dict, identifier: str, key: str, callback: Any, kwargs: dict) -> None:
        self.state, self.identifier, self.key, self.callback, self.kwargs = state, identifier, key, callback, kwargs

    def enable(self) -> None:
        self.state["keybinds"][self.key] = self.callback

    def disable(self) -> None:
        self.state["keybinds"].pop(self.key, None)


def mapping(action: str, key: str) -> Any:
    return types.SimpleNamespace(Action=types.SimpleNamespace(Name=action), Key=types.SimpleNamespace(KeyName=key))


class FakeJumpGoal:
    """A jump definition behind a kept pointer: shared, so every read sees every write."""

    def __init__(self, velocity: float, height: float, use_velocity: bool) -> None:
        self.InitialZVelocity, self.GoalHeight, self.bUseInitialZVelocity = velocity, height, use_velocity


def jump_goals() -> dict[str, Any]:
    """The five definitions with the values read in game on 2026-09-16."""
    return {
        "DefaultJump": FakeJumpGoal(840.0, 198.0, False),
        "SprintJump": FakeJumpGoal(735.0, 198.0, True),
        "DoubleJump": FakeJumpGoal(940.0, 225.0, True),
        "SlideJump": FakeJumpGoal(735.0, 190.0, True),
        "UpwardLadderJump": FakeJumpGoal(700.0, 175.0, True),
    }


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
        self.ReplicatedMantleState = types.SimpleNamespace(ActionIndex=-1)
        self.mantle_allowed = False
        self.LadderState = types.SimpleNamespace(OverlappingClimbables=[])
        self.goals = jump_goals()
        self.type_sets: list[str] = []
        self.CurrentJump = types.SimpleNamespace(
            JumpType=types.SimpleNamespace(TagName="Movement.JumpType.DefaultJump"), JumpGoal=self.goals["DefaultJump"],
        )

    def CanStartPassiveMantle(self) -> bool:
        return self.mantle_allowed

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


def install() -> dict:
    """Registers the fake modules and returns the state the tests read and drive."""
    state: dict = {"misc": [], "warnings": [], "errors": [], "pc": None, "settings_exists": True,
                   "settings_enabled": False, "mods": []}
    state["objects"] = {("OakControlledMove", SLIDE_PATH): FakeSlideAsset(), ("OakControlledMove", DASH_PATH): FakeDashAsset(),
                        ("AnimSequence", CLIMB_ANIMATION_PATH): FakeSequence(0.6)}
    state["anim_instances"] = []
    state["anim_scans"] = 0
    # Enhanced Input: the players' subsystems, the interface's injection function and every injected press.
    state["subsystems"] = []
    state["subsystem_scans"] = 0
    state["inject_function"] = types.SimpleNamespace(Name="InjectInputVectorForAction")
    state["injections"] = []

    def find_all(class_name: str, exact: bool = True) -> Any:
        if class_name == "/Script/EnhancedInput.EnhancedInputLocalPlayerSubsystem":
            state["subsystem_scans"] += 1
            return iter(list(state["subsystems"]))
        state["anim_scans"] += 1
        return iter(list(state["anim_instances"]) if class_name == "/Script/Engine.AnimInstance" else [])
    state["finds"] = 0
    state["keybinds"] = {}
    state["kismet"] = FakeKismet()
    state["class_finds"] = 0

    def find_class(name: str) -> Any:
        if name == "EnhancedInputSubsystemInterface" and state["inject_function"] is not None:
            return types.SimpleNamespace(_find=lambda function: state["inject_function"])
        state["class_finds"] += 1
        if name != "KismetSystemLibrary":
            raise ValueError(f"no class {name}")
        return types.SimpleNamespace(ClassDefaultObject=state["kismet"])

    class BoundFunction:
        def __init__(self, function: Any, target: Any) -> None:
            self.function, self.target = function, target

        def __call__(self, **kwargs: Any) -> None:
            state["injections"].append((self.function, self.target, kwargs))
    state["mappings"] = [
        mapping("Action_Crouch_Hold", "LeftControl"),
        mapping("Action_Crouch_Hold", "Gamepad_FaceButton_Right"),
        mapping("Action_CrouchOrDash", "Gamepad_FaceButton_Right"),
        mapping("Action_Jump_HoldToGlide", "Gamepad_FaceButton_Bottom"),
        mapping("Action_Jump_HoldToGlide", "SpaceBar"),
    ]

    def find_object(class_name: str, path: str) -> Any:
        state["finds"] += 1
        found = state["objects"].get((class_name, path))
        if found is None:
            raise ValueError(f"no object {path}")
        return found

    logging_module = types.ModuleType("unrealsdk.logging")
    logging_module.misc = lambda text: state["misc"].append(text)
    logging_module.warning = lambda text: state["warnings"].append(text)
    logging_module.error = lambda text: state["errors"].append(text)
    logging_module.info = lambda text: state["misc"].append(text)

    class WeakPointer:
        """As pyunrealsdk's (sdk_mods/.stubs/unrealsdk/unreal/_weak_pointer.pyi): calling it gives the object back, or
        None once the game destroyed it. A test destroys one by clearing `obj`."""

        def __init__(self, obj: Any = None) -> None:
            self.obj = obj

        def __call__(self) -> Any:
            return self.obj

    unreal_module = types.ModuleType("unrealsdk.unreal")
    unreal_module.BoundFunction = BoundFunction
    unreal_module.WeakPointer = WeakPointer

    hooks_module = types.ModuleType("unrealsdk.hooks")
    hooks_module.Type = types.SimpleNamespace(POST="POST", PRE="PRE")
    hooks_module.Block = type("Block", (), {})

    unrealsdk_module = types.ModuleType("unrealsdk")
    unrealsdk_module.logging = logging_module
    unrealsdk_module.hooks = hooks_module
    unrealsdk_module.unreal = unreal_module
    unrealsdk_module.find_object = find_object
    unrealsdk_module.find_class = find_class
    unrealsdk_module.find_all = find_all
    unrealsdk_module.make_struct = lambda name, **fields: types.SimpleNamespace(**fields)

    mods_base = types.ModuleType("mods_base")
    mods_base.BoolOption = FakeOption
    mods_base.SliderOption = FakeOption
    mods_base.NestedOption = FakeNested
    mods_base.get_pc = lambda **kwargs: state["pc"]
    mods_base.hook = lambda path, kind, hook_identifier="": (lambda fn: FakeHook(fn, path, hook_identifier))

    def build_mod(cls: type = FakeMod, **kwargs: Any) -> FakeMod:
        # As mods_base: registered, then its settings loaded, and a file that says enabled enables it right here,
        # before build_mod returns (mod_factory.py:149, mod_list.py:47, settings.py:71).
        made = cls(state, **kwargs)
        state["mods"].append(made)
        # True or False for every mod, or the names of the mods whose own settings file says enabled.
        wanted = state["settings_enabled"]
        if state["settings_exists"] and (wanted is True or (not isinstance(wanted, bool) and kwargs.get("name") in wanted)):
            made.enable()
        return made

    mods_base.Mod = FakeMod
    mods_base.build_mod = build_mod
    mods_base.keybind = lambda identifier, key=None, callback=None, **kwargs: FakeKeybind(
        state, identifier, key, callback, kwargs,
    )

    for name, module in {
        "unrealsdk": unrealsdk_module,
        "unrealsdk.logging": logging_module,
        "unrealsdk.hooks": hooks_module,
        "unrealsdk.unreal": unreal_module,
        "mods_base": mods_base,
    }.items():
        sys.modules[name] = module
    return state


def slide_asset(state: dict) -> Any:
    return state["objects"].get(("OakControlledMove", SLIDE_PATH))


def dash_asset(state: dict) -> Any:
    return state["objects"].get(("OakControlledMove", DASH_PATH))


class FakeLocalPlayer:
    """Compared by identity, as game objects are: each controller has its own local player."""


def use_character(state: dict, character: Any) -> None:
    """The player controller for a character, with its local player and that player's Enhanced Input subsystem."""
    state["pc"] = None if character is None else types.SimpleNamespace(
        OakCharacter=character,
        PlayerInput=types.SimpleNamespace(EnhancedActionMappings=state["mappings"]),
        MinPassiveMantleButtonHoldDuration=0.075,
        Player=FakeLocalPlayer(),
    )
    if character is not None:
        state["subsystems"].append(types.SimpleNamespace(Outer=state["pc"].Player))
