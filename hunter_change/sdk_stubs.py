"""Small SDK fakes for Hunter Change's source tests: the modules the mod imports, recording what it logs."""

import pathlib
import sys
import tempfile
import types
import tempfile
from pathlib import Path
import weakref
from typing import Any

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


class FakeDefPtr:
    """A reference by name and type, as the SDK builds one; `_name` and `_type` as the game's own answer."""

    def __init__(self, name: str, def_type: Any = None) -> None:
        self._name, self._type = name, def_type


class FakeOption:
    """A mods_base option: its value, default and texts, and the mod it belongs to."""

    def __init__(self, identifier: str, value: Any = None, *args: Any, **kwargs: Any) -> None:
        self.identifier, self.value, self.default_value = identifier, value, value
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")
        self.is_hidden = kwargs.get("is_hidden", False)
        self.choices = args[0] if args and isinstance(args[0], (list, tuple)) else kwargs.get("choices")
        self.mod = None


class FakeNestedOption:
    def __init__(self, identifier: str, children: list, **kwargs: Any) -> None:
        self.identifier, self.children = identifier, children
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")


class FakeEnum:
    """An engine enum: each member read as "Enum.member", which the tests compare."""

    def __init__(self, name: str) -> None:
        self.name = name

    def __getattr__(self, member: str) -> str:
        if member.startswith("__"):
            raise AttributeError(member)
        return f"{self.name}.{member}"


class FakeHook:
    def __init__(self, fn: Any, identifier: str) -> None:
        self.fn, self.identifier, self.enabled = fn, identifier, False

    def __call__(self, *args: Any) -> Any:
        return self.fn(*args)

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False


class FakeMod:
    def __init__(self, state: dict, **kwargs: Any) -> None:
        self.state, self.kwargs, self.is_enabled = state, kwargs, False
        self._settings_directory = tempfile.TemporaryDirectory()
        self.settings_file = Path(self._settings_directory.name) / "settings.json"
        if state["settings_exists"]:
            self.settings_file.write_text("{}")
        for option in kwargs.get("options", ()):
            option.mod = self

    def save_settings(self) -> None:
        self.state["settings_saves"] += 1

    def iter_display_options(self):
        yield from self.kwargs.get("options", ())

    def enable(self) -> None:
        if self.is_enabled:
            return
        self.is_enabled = True
        for hook in self.kwargs.get("hooks", ()):
            hook.enable()
        if self.kwargs.get("on_enable"):
            self.kwargs["on_enable"]()

    def disable(self) -> None:
        if not self.is_enabled:
            return
        self.is_enabled = False
        for hook in self.kwargs.get("hooks", ()):
            hook.disable()
        if self.kwargs.get("on_disable"):
            self.kwargs["on_disable"]()


def install() -> dict:
    """Registers the fake modules and returns the state the tests read: logs, errors, the controller, the mods built,
    and a fresh settings folder."""
    state: dict = {"logs": [], "errors": [], "pc": None, "mods": [], "settings_exists": False, "structs": [],
                   "settings_saves": 0, "commands": {}, "settings_dir": pathlib.Path(tempfile.mkdtemp())}

    logging = types.ModuleType("unrealsdk.logging")
    logging.info = logging.misc = lambda message: state["logs"].append(message)
    logging.error = lambda message: state["errors"].append(message)
    hooks = types.ModuleType("unrealsdk.hooks")
    hooks.Type = types.SimpleNamespace(POST="POST", PRE="PRE")
    unreal = types.ModuleType("unrealsdk.unreal")
    unreal.WeakPointer = weakref.ref
    unreal.FGbxDefPtr = FakeDefPtr
    sdk = types.ModuleType("unrealsdk")
    sdk.logging, sdk.hooks, sdk.unreal = logging, hooks, unreal

    def make_struct(name: str, **fields: Any) -> Any:
        made = types.SimpleNamespace(struct=name, **fields)
        state["structs"].append(made)
        return made

    sdk.make_struct = make_struct
    sdk.find_enum = FakeEnum
    sdk.find_class = lambda name: types.SimpleNamespace(_path_name=lambda: f"/Script/Stub.{name}")
    sdk.find_all = lambda *_args, **_kwargs: []
    sdk.construct_object = lambda kind, owner: types.SimpleNamespace(kind=kind, owner=owner)
    commands = types.ModuleType("unrealsdk.commands")
    commands.add_command = lambda name, callback, *args: state["commands"].__setitem__(name, callback)
    commands.has_command = lambda name: name in state["commands"]
    commands.remove_command = lambda name: state["commands"].pop(name, None)
    sdk.commands = commands

    mods_base = types.ModuleType("mods_base")
    mods_base.SETTINGS_DIR = state["settings_dir"]
    mods_base.BoolOption = mods_base.SliderOption = mods_base.SpinnerOption = FakeOption
    mods_base.NestedOption = FakeNestedOption
    mods_base.open_in_mod_dir = lambda path, binary=False: open(path, "rb" if binary else "r")
    mods_base.get_pc = lambda **_kwargs: state["pc"]
    mods_base.hook = lambda _path, _kind, hook_identifier="": (lambda fn: FakeHook(fn, hook_identifier))

    def build_mod(cls: type = FakeMod, **kwargs: Any) -> FakeMod:
        made = cls(state, **kwargs)
        state["mods"].append(made)
        return made

    mods_base.Mod = FakeMod
    mods_base.build_mod = build_mod
    # No test reads the real registry: Steam's connected account stays unknown unless a test fakes it
    # (steam_account.py; final review of 2026-09-29 found one test reading it).
    registry = types.ModuleType("winreg")
    registry.HKEY_CURRENT_USER, registry.REG_DWORD = "HKCU", 4

    def no_registry(*_args: Any) -> Any:
        raise FileNotFoundError(2, "no registry in the tests")

    registry.OpenKey = registry.QueryValueEx = no_registry
    for name, module in (("mods_base", mods_base), ("unrealsdk", sdk), ("unrealsdk.logging", logging),
                         ("unrealsdk.hooks", hooks), ("unrealsdk.unreal", unreal), ("unrealsdk.commands", commands),
                         ("winreg", registry)):
        sys.modules[name] = module
    return state
