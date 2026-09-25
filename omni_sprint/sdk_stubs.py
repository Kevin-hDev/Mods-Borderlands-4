"""Fake SDK modules and a fake game memory, so Omni Sprint's logic can be tested outside the game.

Installed into sys.modules before importing omni_sprint. The memory holds a movement component pointing to its
definition, laid out as the SDK's type says, with the game files' values (2026-09-19, verified in game): tests read and
write it through omni_sprint.memory once patch_memory() has swapped the Windows calls for this one.
"""

import struct
import sys
import types
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

LIMIT_OFFSET = 580
# Case as the SDK gives the names; the mod lowers them. The limit sits at 580 as in the 2026-06-26 build.
FIELD_NAMES = (
    "MaxSprintAngle", "SprintAnalogInputThreshold", "MaxSpeedCooldownMaxSpeed", "MaxLadderSlideDownSpeed",
    "FallDelayGravityScale", "MaxLadderDescendSpeed", "LadderSlideAcceleration", "PushAwayFromPlayersRadiusThreshold",
    "DoubleJumpInputDelay", "LadderBrakingDeceleration", "LadderFriction", "LadderSlideBrakingDeceleration",
    "FallDelayTime", "DashInputDelay", "MaxLadderForwardSpeed", "MaxLadderReverseSpeed", "MaxLadderAscendSpeed",
    "JumpQueueTime", "SprintingJumpMaxSpeedPct", "LadderJumpVelocity", "LadderInterpSpeed",
)
OFFSETS = {name: (LIMIT_OFFSET if index == 0 else 16 + index * 8) for index, name in enumerate(FIELD_NAMES)}
BASE = 0x2000_0000
SIZE = 0x40000


class FakeMemory:
    """A block of the game's memory: reads and writes outside it fail, like the Windows calls on a bad address."""

    def __init__(self) -> None:
        self.data = bytearray(SIZE)
        self.refuse_writes = False
        self.writes = 0

    def _inside(self, address: int, size: int) -> bool:
        return BASE <= address and address + size <= BASE + SIZE

    def read(self, address: int, size: int) -> bytes | None:
        return bytes(self.data[address - BASE : address - BASE + size]) if self._inside(address, size) else None

    def write(self, address: int, data: bytes) -> bool:
        if self.refuse_writes or not self._inside(address, len(data)):
            return False
        self.writes += 1
        self.data[address - BASE : address - BASE + len(data)] = data
        return True

    def put_float(self, address: int, value: float) -> None:
        struct.pack_into("<f", self.data, address - BASE, value)

    def get_float(self, address: int) -> float:
        return struct.unpack_from("<f", self.data, address - BASE)[0]

    def put_pointer(self, address: int, value: int) -> None:
        struct.pack_into("<Q", self.data, address - BASE, value)

    def put_definition(self, address: int, known: dict[str, float]) -> None:
        for name, offset in OFFSETS.items():
            self.put_float(address + offset, known[name.lower()])


def movement_type() -> Any:
    """OakCharacterMovementDef as the SDK lists it, with one field the mod does not know."""
    fields = [types.SimpleNamespace(Name=name, Offset_Internal=offset) for name, offset in OFFSETS.items()]
    fields.append(types.SimpleNamespace(Name="bCanClimbLadders", Offset_Internal=900))
    return types.SimpleNamespace(Name="OakCharacterMovementDef", _properties=lambda: iter(fields))


class FakePlayer:
    def __init__(self, fov: float) -> None:
        self.BaseFOV = fov

    def _get_address(self) -> int:
        return id(self)


def player(component: int, fov: float = 90.0) -> Any:
    """A player controller whose character's movement component sits at this address, the menu's FOV in
    Player.BaseFOV."""
    movement = types.SimpleNamespace(_get_address=lambda: component)
    return types.SimpleNamespace(OakCharacter=types.SimpleNamespace(CharacterMovement=movement),
                                 Player=FakePlayer(fov))


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

    logging_module = types.ModuleType("unrealsdk.logging")
    logging_module.misc = lambda text: state["misc"].append(text)
    logging_module.info = lambda text: state["misc"].append(text)
    logging_module.warning = lambda text: state["warnings"].append(text)
    logging_module.error = lambda text: state["errors"].append(text)

    hooks_module = types.ModuleType("unrealsdk.hooks")
    hooks_module.Type = types.SimpleNamespace(POST="POST", PRE="PRE")

    unrealsdk_module = types.ModuleType("unrealsdk")
    unrealsdk_module.logging = logging_module
    unrealsdk_module.hooks = hooks_module
    unrealsdk_module.find_all = find_all
    unrealsdk_module.make_struct = lambda name, **fields: types.SimpleNamespace(**fields)
    unreal_module = types.ModuleType("unrealsdk.unreal")
    unreal_module.WeakPointer = weakref.ref
    unrealsdk_module.unreal = unreal_module

    mods_base = types.ModuleType("mods_base")
    mods_base.get_pc = lambda **kwargs: state["pc"]
    mods_base.BoolOption = FakeOption
    mods_base.KeybindOption = FakeKeybindOption
    mods_base.NestedOption = FakeNestedOption
    mods_base.SliderOption = FakeOption
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


def patch_memory(memory_module: Any, fake: FakeMemory) -> None:
    memory_module.read, memory_module.write = fake.read, fake.write
