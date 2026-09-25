"""Fake SDK modules so Vehicle Driving's logic can be tested outside the game.

Installed into sys.modules before importing vehicle_driving. Cut down from Apex Movement's to what this mod calls:
options, the frame hook, the mod, weak pointers, the log, one trace and the player controller. The vehicle and its
driver carry the values sessions 1 to 9 read on Kevin's vehicle (2026-09-18).
"""

import sys
import types
from typing import Any


class FakeOption:
    def __init__(self, identifier: str, value: Any, *args: Any, **kwargs: Any) -> None:
        # args holds a slider's bounds, in mods_base's order: min_value, max_value.
        self.identifier, self.value, self.args, self.kwargs = identifier, value, args, kwargs
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")
        self.step = kwargs.get("step", 1)
        self.is_integer = kwargs.get("is_integer", True)
        # mods_base's names for a slider's bounds and first value; a switch has no bounds.
        self.min_value, self.max_value = (args + (None, None))[:2]
        self.default_value = value


class FakeNestedOption:
    def __init__(self, identifier: str, children: list, **kwargs: Any) -> None:
        self.identifier, self.children = identifier, children
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")


class FakeHook:
    def __init__(self, fn: Any, path: str, kind: str, identifier: str) -> None:
        self.fn, self.path, self.kind, self.identifier, self.enabled = fn, path, kind, identifier, False

    def __call__(self, *args: Any) -> Any:
        return self.fn(*args)

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False


class FakeMod:
    """As mods_base.Mod where this mod depends on it: hooks on before on_enable, off before on_disable."""

    def __init__(self, state: dict, **kwargs: Any) -> None:
        self.state, self.kwargs, self.is_enabled = state, kwargs, False
        self.settings_file = types.SimpleNamespace(exists=lambda: state["settings_exists"])

    def enable(self) -> None:
        if self.is_enabled:
            return
        self.is_enabled = True
        for hook in self.kwargs.get("hooks") or []:
            hook.enable()
        if self.kwargs.get("on_enable"):
            self.kwargs["on_enable"]()

    def disable(self) -> None:
        if not self.is_enabled:
            return
        self.is_enabled = False
        for hook in self.kwargs.get("hooks") or []:
            hook.disable()
        if self.kwargs.get("on_disable"):
            self.kwargs["on_disable"]()

    def save_settings(self) -> None:
        self.state["saves"] = self.state.get("saves", 0) + 1

    def iter_display_options(self):
        yield from self.kwargs.get("options", ())


class WeakPointer:
    """As pyunrealsdk's (sdk_mods/.stubs/unrealsdk/unreal/_weak_pointer.pyi): calling it gives the object back, or
    None once the game destroyed it, even for a pointer made afterwards; destroy() stands for the game destroying an
    object."""

    made: list["WeakPointer"] = []
    destroyed: list[Any] = []

    def __init__(self, obj: Any = None) -> None:
        self.obj = None if any(obj is gone for gone in WeakPointer.destroyed) else obj
        WeakPointer.made.append(self)

    def __call__(self) -> Any:
        return self.obj


def destroy(obj: Any) -> None:
    WeakPointer.destroyed.append(obj)
    for pointer in WeakPointer.made:
        if pointer.obj is obj:
            pointer.obj = None


class Ground:
    """KismetSystemLibrary's class default object: the trace meets the ground `below` under its start, or nothing
    when below is None or beyond the trace's end."""

    def __init__(self) -> None:
        self.below: float | None = 60.0
        self.calls: list[tuple] = []

    def LineTraceSingle(self, context: Any, start: Any, end: Any, channel: int, complex_trace: bool, ignored: list,
                        draw: int, out: Any, ignore_self: bool, *tail: Any) -> tuple:
        self.calls.append((context, start, end, channel, ignore_self, len(tail)))
        if self.below is None or self.below > start.Z - end.Z:
            return False, [], types.SimpleNamespace(Distance=0.0)
        return True, [], types.SimpleNamespace(Distance=self.below)


def vector(x: float, y: float, z: float = 0.0) -> Any:
    return types.SimpleNamespace(X=x, Y=y, Z=z)


def rotator(yaw: float) -> Any:
    return types.SimpleNamespace(Pitch=0.0, Yaw=yaw, Roll=0.0)


class Mesh:
    """The vehicle's physics body: a velocity set is what the next frame reads."""

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> None:
        self.velocity = vector(x, y, z)
        self.sets: list[tuple] = []

    def GetPhysicsLinearVelocity(self, bone: str) -> Any:
        return self.velocity

    def SetPhysicsLinearVelocity(self, velocity: Any, add: bool, bone: str) -> None:
        self.sets.append((velocity, add, bone))
        self.velocity = velocity


def springs(*stiffness: float) -> Any:
    return types.SimpleNamespace(Springs=[types.SimpleNamespace(Stiffness=value) for value in stiffness])


def pair(value: float, base: float) -> Any:
    return types.SimpleNamespace(Value=value, BaseValue=base)


class Driver:
    """The player's character at the wheel: its driving attributes, base and value with Kevin's Hover Drive."""

    def __init__(self) -> None:
        self.Name = "OakCharacter_1"
        attributes = types.SimpleNamespace(maxspeed=pair(51.3194, 50.0), BoostMaxSpeed=pair(66.3425, 65.0),
                                           MaxAccel=pair(1286.48, 1000.0), BoostMaxAccel=pair(1615.08, 1200.0))
        self.VehicleDriverComponent = types.SimpleNamespace(VehicleAttributesState=attributes)


class Vehicle:
    """A vehicle: springs and jump on its movement's HoverSetup, a physics body, a driver."""

    def __init__(self, name: str = "OakVehicle_1", driver: Any = None, yaw: float = 0.0, slide: str = "None") -> None:
        self.Name = name
        self.yaw = yaw
        self.location = vector(100.0, 200.0, 22.0)
        self.Mesh = Mesh()
        hover = types.SimpleNamespace(YawSpring_Idle=springs(5.0), YawSpring_Hovering=springs(3.0, 3.5, 4.0),
                                      YawSpring_Boosting=springs(1.0, 1.7, 2.4),
                                      PowerslideJumpHeight=types.SimpleNamespace(constant=165.0))
        self.OakVehicleMovement = types.SimpleNamespace(HoverSetup=hover,
                                                        PowerslideInput=types.SimpleNamespace(name=slide))
        self.DriverPawn = driver if driver is not None else Driver()

    def K2_GetActorRotation(self) -> Any:
        return rotator(self.yaw)

    def K2_GetActorLocation(self) -> Any:
        return self.location


def install() -> dict:
    """Registers the fake modules and returns the state the tests read and drive."""
    state: dict = {"misc": [], "warnings": [], "errors": [], "pc": None, "settings_exists": True,
                   "settings_enabled": False, "mods": [], "keybinds": [], "ground": Ground(), "class_finds": 0}

    def find_class(name: str) -> Any:
        state["class_finds"] += 1
        if name != "KismetSystemLibrary":
            raise ValueError(f"no class {name}")
        return types.SimpleNamespace(ClassDefaultObject=state["ground"])

    logging_module = types.ModuleType("unrealsdk.logging")
    logging_module.misc = lambda text: state["misc"].append(text)
    logging_module.info = lambda text: state["misc"].append(text)
    logging_module.warning = lambda text: state["warnings"].append(text)
    logging_module.error = lambda text: state["errors"].append(text)

    unreal_module = types.ModuleType("unrealsdk.unreal")
    unreal_module.WeakPointer = WeakPointer

    hooks_module = types.ModuleType("unrealsdk.hooks")
    hooks_module.Type = types.SimpleNamespace(POST="POST", PRE="PRE")

    unrealsdk_module = types.ModuleType("unrealsdk")
    unrealsdk_module.logging = logging_module
    unrealsdk_module.hooks = hooks_module
    unrealsdk_module.unreal = unreal_module
    unrealsdk_module.find_class = find_class
    unrealsdk_module.make_struct = lambda name, **fields: types.SimpleNamespace(**fields)

    mods_base = types.ModuleType("mods_base")
    mods_base.BoolOption = FakeOption
    mods_base.SliderOption = FakeOption
    mods_base.NestedOption = FakeNestedOption
    mods_base.get_pc = lambda **kwargs: state["pc"]
    mods_base.hook = lambda path, kind, hook_identifier="": (lambda fn: FakeHook(fn, path, kind, hook_identifier))
    mods_base.keybind = lambda *args, **kwargs: state["keybinds"].append((args, kwargs))

    def build_mod(cls: type = FakeMod, **kwargs: Any) -> FakeMod:
        # As mods_base: registered, then its settings loaded, and a file that says enabled enables it right here.
        made = cls(state, **kwargs)
        state["mods"].append(made)
        if state["settings_exists"] and state["settings_enabled"]:
            made.enable()
        return made

    mods_base.build_mod = build_mod

    for name, module in {
        "unrealsdk": unrealsdk_module,
        "unrealsdk.logging": logging_module,
        "unrealsdk.hooks": hooks_module,
        "unrealsdk.unreal": unreal_module,
        "mods_base": mods_base,
    }.items():
        sys.modules[name] = module
    return state
