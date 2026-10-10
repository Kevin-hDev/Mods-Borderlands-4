"""Fake SDK modules, so Omni Sprint's logic can be tested outside the game.

Installed into sys.modules before importing omni_sprint. The fake game memory, which holds the movement definition the
shared runtime opens since 2026-10-09, is the shared runtime's own (sprint_memory_fixtures.py).
"""

import sys
import types
import tempfile
import weakref
from pathlib import Path
from typing import Any

from sdk_stubs_keybinds import FakeKeybind
from sdk_stubs_options import FakeKeybindOption, FakeNestedOption, FakeOption

# The camera runtime sits beside the mods: camera_runtime/source in the workshop, camera_runtime in the public copy.
_HERE = Path(__file__).resolve().parent
RUNTIME_SOURCE = next((path for path in (_HERE.parent.parent / "camera_runtime" / "source",
                                         _HERE.parent / "camera_runtime") if path.is_dir()),
                      _HERE.parent.parent / "camera_runtime" / "source")
if str(RUNTIME_SOURCE) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SOURCE))

from sprint_memory_fixtures import BASE, OFFSETS, FakeMemory, movement_type, patch  # noqa: E402,F401


class FakePlayer:
    def __init__(self, fov: float) -> None:
        self.BaseFOV = fov

    def _get_address(self) -> int:
        return id(self)


def player(component: int, fov: float = 90.0) -> Any:
    """A player controller whose character's movement component sits at this address, the menu's FOV in
    Player.BaseFOV, and its body's animation in OakCharacter.Mesh (the clock counts that body's updates only)."""
    movement = types.SimpleNamespace(_get_address=lambda: component, bIsSprinting=False, MovementMode=1)
    body = types.SimpleNamespace(_get_address=lambda: component + 0x800)
    mesh = types.SimpleNamespace(GetAnimInstance=lambda: body)
    character = types.SimpleNamespace(CharacterMovement=movement, Mesh=mesh)
    return types.SimpleNamespace(OakCharacter=character, Player=FakePlayer(fov))


def body(pc: Any) -> Any:
    """The played body's animation, whose updates tick the clock."""
    return pc.OakCharacter.Mesh.GetAnimInstance()


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
        self._settings_directory = tempfile.TemporaryDirectory()
        self.settings_file = Path(self._settings_directory.name) / "settings.json"
        if state["settings_exists"]:
            self.settings_file.write_text("{}")
        for option in kwargs.get("options") or []:
            option.mod = self

    def save_settings(self) -> None:
        self.state["settings_saves"] += 1

    def iter_display_options(self):
        yield from self.kwargs.get("options", ())

    def enable(self) -> None:
        if self.is_enabled:
            return
        self.is_enabled = True
        for hook in self.kwargs.get("hooks") or []:
            hook.enable()
        for bind in self.kwargs.get("keybinds") or []:
            bind.enable()
        if self.kwargs.get("on_enable"):
            self.kwargs["on_enable"]()

    def disable(self) -> None:
        if not self.is_enabled:
            return
        self.is_enabled = False
        for hook in self.kwargs.get("hooks") or []:
            hook.disable()
        for bind in self.kwargs.get("keybinds") or []:
            bind.disable()
        if self.kwargs.get("on_disable"):
            self.kwargs["on_disable"]()


def install() -> dict:
    """Registers the fake modules and returns the state the tests read and drive."""
    state: dict = {"misc": [], "warnings": [], "errors": [], "pc": None, "settings_exists": True,
                   "settings_enabled": False, "settings_saves": 0, "mods": [], "keybinds": {},
                   "types": [movement_type()], "type_finds": 0}

    def find_all(cls: str, exact: bool = True) -> Any:
        state["type_finds"] += 1
        return iter([types.SimpleNamespace(Name="Vector", _properties=lambda: iter([])), *state["types"]])

    def unknown_object(*args: Any, **kwargs: Any) -> Any:
        return None

    logging_module = types.ModuleType("unrealsdk.logging")
    logging_module.misc = lambda text: state["misc"].append(text)
    logging_module.info = lambda text: state["misc"].append(text)
    logging_module.warning = lambda text: state["warnings"].append(text)
    logging_module.error = lambda text: state["errors"].append(text)

    hooks_module = types.ModuleType("unrealsdk.hooks")
    hooks_module.Type = types.SimpleNamespace(POST="POST", PRE="PRE")
    # The camera runtime's own clock at the wheel (vehicle_framing.py) installs its hook through these.
    installed = state.setdefault("hooks", {})
    hooks_module.add_hook = lambda path, kind, identifier, callback: installed.__setitem__(
        (path, kind, identifier), callback)
    hooks_module.has_hook = lambda path, kind, identifier: (path, kind, identifier) in installed
    hooks_module.remove_hook = lambda path, kind, identifier: installed.pop((path, kind, identifier))

    unrealsdk_module = types.ModuleType("unrealsdk")
    unrealsdk_module.logging = logging_module
    unrealsdk_module.hooks = hooks_module
    unrealsdk_module.find_all = find_all
    unrealsdk_module.make_struct = lambda name, **fields: types.SimpleNamespace(**fields)
    unrealsdk_module.find_object = unknown_object
    unrealsdk_module.construct_object = unknown_object
    unreal_module = types.ModuleType("unrealsdk.unreal")
    unreal_module.WeakPointer = weakref.ref
    unrealsdk_module.unreal = unreal_module

    mods_base = types.ModuleType("mods_base")
    mods_base.get_pc = lambda **kwargs: state["pc"]
    mods_base.BoolOption = FakeOption
    mods_base.KeybindOption = FakeKeybindOption
    mods_base.NestedOption = FakeNestedOption
    mods_base.SliderOption = FakeOption
    mods_base.SpinnerOption = FakeOption
    mods_base.EInputEvent = types.SimpleNamespace(IE_Pressed="IE_Pressed")
    mods_base.hook = lambda path, kind, hook_identifier="": (lambda fn: FakeHook(fn, path, kind, hook_identifier))
    mods_base.keybind = lambda identifier, key=None, callback=None, **kwargs: FakeKeybind(
        state, identifier, key, callback, kwargs)

    def build_mod(cls: type = FakeMod, **kwargs: Any) -> FakeMod:
        # As mods_base: registered, then its settings loaded, and a file that says enabled enables it right here.
        made = cls(state, **kwargs)
        state["mods"].append(made)
        if state["settings_exists"] and state["settings_enabled"]:
            made.enable()
        return made

    mods_base.Mod = FakeMod
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
