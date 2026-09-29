"""Fake SDK modules so the probe's logic can be tested outside the game.

Installed into sys.modules before importing apex_probe, the way test_auto_sprint.py does it.
"""

import enum
import sys
import types
from typing import Any

LOG_FILE_NAME = "apex_probe.log"


class FakeHook:
    def __init__(self, fn: Any, state: dict, identifier: str) -> None:
        self.fn, self.state, self.identifier, self.enabled = fn, state, identifier, False

    def enable(self) -> None:
        self.enabled = True
        self.state["hooks"][self.identifier] = self

    def disable(self) -> None:
        self.enabled = False
        self.state["hooks"].pop(self.identifier, None)


class FakePath:
    """Stands in for MODS_DIR: remembers what was written instead of touching the disk."""

    def __init__(self, state: dict, name: str) -> None:
        self.state, self.name = state, name

    def __truediv__(self, other: str) -> "FakePath":
        return FakePath(self.state, other)

    def open(self, mode: str = "r", encoding: str | None = None) -> Any:
        state, name = self.state, self.name

        class Writer:
            def __enter__(self) -> Any:
                return self

            def __exit__(self, *_a: Any) -> None:
                return None

            def write(self, text: str) -> None:
                state["written"].append((name, text))

        return Writer()


class FakeKeybind:
    """Stands in for mods_base.keybind: the tests fire key events by calling state["keybinds"][key]."""

    def __init__(self, state: dict, identifier: str, key: str, callback: Any, event_filter: Any) -> None:
        self.state, self.identifier, self.key, self.callback = state, identifier, key, callback
        self.event_filter, self.is_enabled = event_filter, False

    def enable(self) -> None:
        self.is_enabled = True
        self.state["keybinds"][self.key] = self.callback

    def disable(self) -> None:
        self.is_enabled = False
        self.state["keybinds"].pop(self.key, None)


class FakeCommand:
    """Stands in for a console command: keeps its arguments and stays callable, like mods_base does."""

    def __init__(self, fn: Any) -> None:
        self.fn, self.arguments = fn, []

    def add_argument(self, *args: Any, **kwargs: Any) -> None:
        self.arguments.append((args, kwargs))

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.fn(*args, **kwargs)


class FakeGbxDefPtr:
    """Stands in for unrealsdk.unreal.FGbxDefPtr: a handle whose fields are the game's shared definition itself."""

    def __init__(self, name: str, **values: Any) -> None:
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_values", values)

    def __getattr__(self, name: str) -> Any:
        try:
            return self._values[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name: str, value: Any) -> None:
        if name not in self._values:
            raise AttributeError(name)
        self._values[name] = value

    def __dir__(self) -> list[str]:
        return ["_name", *self._values]


class FakeGameDataHandle(FakeGbxDefPtr):
    """Stands in for unrealsdk.unreal.FGameDataHandle, the other kind of definition reference."""


def vector(x: float, y: float, z: float = 0.0) -> Any:
    return types.SimpleNamespace(X=x, Y=y, Z=z)


def rotator(yaw: float) -> Any:
    return types.SimpleNamespace(Pitch=0.0, Yaw=yaw, Roll=0.0)


def asset_registry(state: dict, load: Any) -> None:
    """Stands in for the engine's AssetRegistryHelpers.GetAsset, apex_held_object's loader: load gets the AssetData,
    and GetAsset gives back its result with the struct, as the game did. The model classes get a made-up path."""
    state["classes"]["AssetRegistryHelpers"] = types.SimpleNamespace(
        ClassDefaultObject=types.SimpleNamespace(GetAsset=lambda data: (load(data), data)))
    for name in ("StaticMesh", "GestaltSkeletalMesh"):
        state["classes"].setdefault(name, types.SimpleNamespace(_path_name=lambda name=name: f"/Script/Stub.{name}"))


class UObject:
    """Stands in for a game object, the way pyunrealsdk's own UObject does: the walk tells one from a struct."""


class FakeClass:
    """Stands in for a game class: the probe walks its fields by name."""

    def __init__(self, name: str, field_names: Any = ()) -> None:
        self.Name = name
        self._props = [types.SimpleNamespace(Name=field) for field in field_names]

    def _properties(self) -> Any:
        return list(self._props)


class FakeObject(UObject):
    """Stands in for a game object the probe inspects: a class, and fields readable by name or by property."""

    def __init__(self, class_name: str, fields: dict | None = None) -> None:
        self.fields = dict(fields or {})
        self.Class = FakeClass(class_name, list(self.fields))

    def _get_field(self, prop: Any) -> Any:
        return self.fields[prop.Name]

    def __getattr__(self, name: str) -> Any:
        fields = self.__dict__.get("fields", {})
        if name in fields:
            return fields[name]
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any) -> None:
        # Writing a field writes the field, as it does in the game: a test reads back what the mod wrote.
        fields = self.__dict__.get("fields")
        if fields is not None and name in fields:
            fields[name] = value
        else:
            object.__setattr__(self, name, value)


class FakePawn(FakeObject):
    """A character other than the player: a name of its own, a place, a speed, an AI controller and its dodge.

    In Borderlands 4 every one of them wears the same class and differs by its name (Char_CatElder_2147453215),
    which is why the name is what the probe reads (session of 2026-09-20).
    """

    def __init__(self, name: str = "Char_Enemy_2147450001", location: Any = None, speed: float = 0.0,
                 mode: str = "<EMovementMode.MOVE_Walking: 1>", fields: dict | None = None,
                 movement_fields: dict | None = None, controller: str = "AIController",
                 class_name: str = "OakCharacter", dodge: Any = None) -> None:
        held = dict(fields or {})
        if dodge is not None:
            held["AIDodgeState"] = types.SimpleNamespace(CurrentDodgeData=dodge)
        super().__init__(class_name, held)
        self.Name = name
        self.location = location if location is not None else vector(0.0, 0.0, 0.0)
        self.CharacterMovement = FakeObject(f"{class_name}Movement", {
            "Velocity": vector(speed, 0.0, 0.0), "MovementMode": mode, **(movement_fields or {})})
        self.Controller = FakeObject(controller)

    def K2_GetActorLocation(self) -> Any:
        return self.location

    def set_speed(self, speed: float) -> None:
        self.CharacterMovement.fields["Velocity"] = vector(speed, 0.0, 0.0)


class FakeMovement:
    def __init__(self) -> None:
        self.Velocity = vector(0.0, 0.0, 0.0)
        self.MovementMode = "<EMovementMode.MOVE_Walking: 1>"
        self.bIsSprinting = False
        self.bWantsToSlide = False
        self.CurrentJump = types.SimpleNamespace(JumpType="{TagName: 'Movement.JumpType.DefaultJump'}")


class FakeCharacter:
    """A player character whose orientation, view, position and stick input the tests set directly."""

    def __init__(self, anim: Any = None) -> None:
        self.CharacterMovement = FakeMovement()
        self.anim = anim if anim is not None else object()
        self.Mesh = types.SimpleNamespace(GetAnimInstance=lambda: self.anim)
        self.bIsCrouched = False
        self.yaw = 0.0
        self.view_yaw = 0.0
        self.location = vector(0.0, 0.0, 0.0)
        self.input = vector(0.0, 0.0, 0.0)
        self.Controller = types.SimpleNamespace(GetControlRotation=lambda: rotator(self.view_yaw))

    def K2_GetActorRotation(self) -> Any:
        return rotator(self.yaw)

    def K2_GetActorLocation(self) -> Any:
        return self.location

    def GetLastMovementInputVector(self) -> Any:
        return self.input


class FakeStruct:
    """Stands in for a game structure: no Class, its fields come from _type, as apex_object_lines reads them.
    A field holding an Exception raises it when read, as a field Python cannot read does in the game."""

    def __init__(self, fields: dict) -> None:
        self.fields = fields
        self._type = FakeClass("Struct", list(fields))

    def _get_field(self, prop: Any) -> Any:
        value = self.fields[prop.Name]
        if isinstance(value, Exception):
            raise value
        return value


def property_kind(value: Any) -> str:
    """The property class the game gives a field holding such a value."""
    if isinstance(value, bool):
        return "BoolProperty"
    if isinstance(value, int):
        return "IntProperty"
    if isinstance(value, float):
        return "FloatProperty"
    if isinstance(value, str):
        return "NameProperty"
    if isinstance(value, FakeStruct):
        return "StructProperty"
    if isinstance(value, list):
        return "ArrayProperty"
    return "ObjectProperty"


def typed(target: Any, **kinds: str) -> Any:
    """Gives each field of a fake object or struct the property class the game would; kinds overrides some by name."""
    owner = target._type if isinstance(target, FakeStruct) else target.Class
    owner._props = [types.SimpleNamespace(Name=prop.Name, Class=types.SimpleNamespace(
        Name=kinds.get(prop.Name) or property_kind(target.fields[prop.Name]))) for prop in owner._props]
    return target


def install(character: Any | None = None) -> dict:
    """Registers the fake modules and returns the state the tests read."""
    state: dict = {
        "misc": [],
        "info": [],
        "errors": [],
        "hooks": {},
        "written": [],
        "pc": None,
        "classes": {},
        "objects": {},
        "enums": {},
        "all": {},
        "keybinds": {},
    }
    if character is not None:
        state["pc"] = types.SimpleNamespace(OakCharacter=character)

    logging_module = types.ModuleType("unrealsdk.logging")
    logging_module.misc = lambda text: state["misc"].append(text)
    logging_module.info = lambda text: state["info"].append(text)
    logging_module.error = lambda text: state["errors"].append(text)

    hooks_module = types.ModuleType("unrealsdk.hooks")
    hooks_module.Type = types.SimpleNamespace(POST="POST", PRE="PRE")
    hooks_module.Block = type("Block", (), {})

    unreal_module = types.ModuleType("unrealsdk.unreal")
    unreal_module.UObject = UObject
    unreal_module.FGbxDefPtr = FakeGbxDefPtr
    unreal_module.FGameDataHandle = FakeGameDataHandle

    unrealsdk_module = types.ModuleType("unrealsdk")
    unrealsdk_module.logging = logging_module
    unrealsdk_module.hooks = hooks_module
    unrealsdk_module.unreal = unreal_module
    unrealsdk_module.find_class = lambda name, **k: state["classes"][name]
    unrealsdk_module.find_all = lambda name, exact=True: iter(state["all"].get(name, []))
    unrealsdk_module.find_object = lambda cls, path: state["objects"][path]
    unrealsdk_module.find_enum = lambda name, **k: state["enums"][name]
    unrealsdk_module.make_struct = lambda name, **kwargs: types.SimpleNamespace(**kwargs)

    mods_base = types.ModuleType("mods_base")
    mods_base.MODS_DIR = FakePath(state, "mods_dir")
    mods_base.get_pc = lambda **k: state["pc"]
    mods_base.hook = lambda path, kind, hook_identifier="": (
        lambda fn: FakeHook(fn, state, hook_identifier or path)
    )
    mods_base.command = lambda name, description="": (lambda fn: FakeCommand(fn))
    # The arguments are kept: a command written but left out of the list reaches no console, and a test checks it.
    mods_base.build_mod = lambda **k: types.SimpleNamespace(settings_file=None, enable=lambda: None, **k)
    mods_base.EInputEvent = enum.Enum("EInputEvent", ["IE_Pressed", "IE_Released", "IE_Repeat", "IE_DoubleClick"])
    mods_base.keybind = lambda identifier, key=None, callback=None, event_filter=None, **k: FakeKeybind(
        state, identifier, key, callback, event_filter
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
