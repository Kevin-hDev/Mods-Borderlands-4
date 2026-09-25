"""Small SDK fakes for Third Person & FOV's source tests."""

import pathlib
import sys
import types
import weakref
from typing import Any

# Tests run beside camera_runtime/source in the workshop and beside camera_runtime in the public repository.
_HERE = pathlib.Path(__file__).resolve().parent
RUNTIME_SOURCE = next((path for path in (_HERE.parent.parent / "camera_runtime" / "source",
                                         _HERE.parent / "camera_runtime") if path.is_dir()),
                      _HERE.parent.parent / "camera_runtime" / "source")
if str(RUNTIME_SOURCE) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SOURCE))


class FakeOption:
    def __init__(self, identifier: str, value: Any, min_value: Any = None, max_value: Any = None,
                 **kwargs: Any) -> None:
        self.identifier, self.value, self.default_value = identifier, value, value
        self.min_value, self.max_value = min_value, max_value
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")
        self.is_hidden = kwargs.get("is_hidden", False)
        self.mod = None


class FakeKeybindOption(FakeOption):
    @classmethod
    def from_keybind(cls, bind: Any):
        option = cls(bind.identifier, bind.key, display_name=bind.display_name,
                     description=bind.description, is_hidden=bind.is_hidden)
        option.on_change_anytime = lambda _option, key: setattr(bind, "key", key)
        return option

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "value" and getattr(self, "on_change_anytime", None) is not None:
            self.on_change_anytime(self, value)
        super().__setattr__(name, value)


class FakeKeybind:
    def __init__(self, state: dict, identifier: str, key: str, callback: Any, kwargs: dict) -> None:
        self.state, self.identifier, self._key, self.callback = state, identifier, key, callback
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")
        self.is_rebindable = kwargs.get("is_rebindable", True)
        self.is_hidden = kwargs.get("is_hidden", False)
        self.enabled = False

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        if self.enabled:
            self.state["keybinds"].pop(self._key, None)
        self._key = value
        if self.enabled and value is not None:
            self.state["keybinds"][value] = self.callback

    def enable(self) -> None:
        self.enabled = True
        if self.key is not None:
            self.state["keybinds"][self.key] = self.callback

    def disable(self) -> None:
        self.state["keybinds"].pop(self.key, None)
        self.enabled = False


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
        self.settings_file = types.SimpleNamespace(exists=lambda: state["settings_exists"])
        for option in kwargs.get("options", ()):
            option.mod = self

    def save_settings(self) -> None:
        if self.state["refuse_save"]:
            raise RuntimeError("save refused")
        self.state["settings_saves"] += 1

    def enable(self) -> None:
        if self.is_enabled:
            return
        self.is_enabled = True
        for hook in self.kwargs.get("hooks", ()):
            hook.enable()
        for bind in self.kwargs.get("keybinds", ()):
            bind.enable()
        if self.kwargs.get("on_enable"):
            self.kwargs["on_enable"]()

    def disable(self) -> None:
        if not self.is_enabled:
            return
        self.is_enabled = False
        for hook in self.kwargs.get("hooks", ()):
            hook.disable()
        for bind in self.kwargs.get("keybinds", ()):
            bind.disable()
        if self.kwargs.get("on_disable"):
            self.kwargs["on_disable"]()


def install() -> dict:
    state = {"logs": [], "errors": [], "keybinds": {}, "mods": [], "pc": None,
             "settings_exists": False, "settings_saves": 0, "refuse_save": False}

    logging = types.ModuleType("unrealsdk.logging")
    logging.info = logging.misc = lambda message: state["logs"].append(message)
    logging.error = lambda message: state["errors"].append(message)
    hooks = types.ModuleType("unrealsdk.hooks")
    hooks.Type = types.SimpleNamespace(POST="POST")
    unreal = types.ModuleType("unrealsdk.unreal")
    unreal.WeakPointer = weakref.ref
    sdk = types.ModuleType("unrealsdk")
    sdk.logging, sdk.hooks, sdk.unreal = logging, hooks, unreal

    mods_base = types.ModuleType("mods_base")
    mods_base.BoolOption = mods_base.SliderOption = FakeOption
    mods_base.KeybindOption = FakeKeybindOption
    mods_base.get_pc = lambda **_kwargs: state["pc"]
    mods_base.keybind = lambda identifier, key=None, callback=None, **kwargs: FakeKeybind(
        state, identifier, key, callback, kwargs)
    mods_base.hook = lambda _path, _kind, hook_identifier="": (
        lambda fn: FakeHook(fn, hook_identifier))

    def build_mod(**kwargs: Any) -> FakeMod:
        made = FakeMod(state, **kwargs)
        state["mods"].append(made)
        return made

    mods_base.build_mod = build_mod
    for name, module in (("mods_base", mods_base), ("unrealsdk", sdk),
                         ("unrealsdk.logging", logging), ("unrealsdk.hooks", hooks),
                         ("unrealsdk.unreal", unreal)):
        sys.modules[name] = module
    return state


def body(name: str, address: int) -> Any:
    return types.SimpleNamespace(
        Class=types.SimpleNamespace(Name=name), _get_address=lambda: address)


def player(body_object: Any, fov: float = 90.0) -> Any:
    mesh = types.SimpleNamespace(GetAnimInstance=lambda: body_object)
    game_player = types.SimpleNamespace(BaseFOV=fov, _get_address=lambda: id(mesh))
    return types.SimpleNamespace(OakCharacter=types.SimpleNamespace(Mesh=mesh), Player=game_player)
