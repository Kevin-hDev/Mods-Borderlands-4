"""Install fake SDK modules so Apex Movement can be tested outside the game."""

import sys
import types
from pathlib import Path
from typing import Any

from sdk_stubs_assets import FakeDashAsset, FakeKeybind, FakeSlideAsset, mapping
from sdk_stubs_core import (
    CLIMB_ANIMATION_PATH, DASH_PATH, SLIDE_PATH, Direction, FakeHook, FakeMod,
    FakeKeybindOption, FakeNested, FakeOption, Mode, vector,
)
from sdk_stubs_player import FakeCharacter, FakeKismet, FakeMovement, FakeSequence, add_arms

# The camera runtime sits beside the mods: camera_runtime/source in the workshop, camera_runtime in the public copy.
_HERE = Path(__file__).resolve().parent
RUNTIME_SOURCE = next((path for path in (_HERE.parent.parent / "camera_runtime" / "source",
                                         _HERE.parent / "camera_runtime") if path.is_dir()),
                      _HERE.parent.parent / "camera_runtime" / "source")
if str(RUNTIME_SOURCE) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SOURCE))

def install() -> dict:
    """Registers the fake modules and returns the state the tests read and drive."""
    state: dict = {"misc": [], "warnings": [], "errors": [], "pc": None, "settings_exists": True,
                   "settings_saves": 0,
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
        if class_name == "OakControlledMove":
            return iter(list(state.get("controlled_moves", [])))
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

    class WeakPointer:
        """As pyunrealsdk's (sdk_mods/.stubs/unrealsdk/unreal/_weak_pointer.pyi): calling it gives the object back, or
        None once the game destroyed it, which a test does with sdk_stubs.destroy."""

        def __init__(self, obj: Any = None) -> None:
            self.obj = obj

        def __call__(self) -> Any:
            return None if getattr(self.obj, "destroyed", False) else self.obj

    unreal_module = types.ModuleType("unrealsdk.unreal")
    unreal_module.BoundFunction = BoundFunction
    unreal_module.WeakPointer = WeakPointer

    hooks_module = types.ModuleType("unrealsdk.hooks")
    hooks_module.Type = types.SimpleNamespace(PRE="PRE", POST="POST")
    hooks_module.Block = type("Block", (), {})
    state["hooks"] = {}
    hooks_module.add_hook = lambda path, kind, identifier, callback: state["hooks"].__setitem__(
        (path, kind, identifier), callback)
    hooks_module.has_hook = lambda path, kind, identifier: (path, kind, identifier) in state["hooks"]
    hooks_module.remove_hook = lambda path, kind, identifier: \
        state["hooks"].pop((path, kind, identifier), None) is not None

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
    mods_base.KeybindOption = FakeKeybindOption
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

    def __init__(self) -> None:
        self.BaseFOV = 90.0

    def _get_address(self) -> int:
        return id(self)


def destroy(character: Any) -> None:
    """The game destroys an object, as a level change destroys the player character: every weak pointer to it then
    answers None, while the Python object stays in the test's hands."""
    character.destroyed = True


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
