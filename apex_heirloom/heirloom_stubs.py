"""The fake SDK of Apex Heirloom's tests: the probes' (mods/perso/apex_probe/source/sdk_stubs.py), with what the mod
needs from mods_base: its options, keys and hooks, and the mod they belong to. Installed before importing
apex_heirloom, whose __init__ builds the mod.

Tidy Weapons brought a fake of its own when it joined the heirloom (2026-09-26): one package takes one fake, so that
each behaviour of mods_base is imitated once, as mods_base/options.py and mod.py do it.
"""

import pathlib
import sys
import types
from typing import Any

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
# The probes' fake SDK sits beside this file in the public copy (publish_repo.py), in the probe's folder here.
if not (HERE / "sdk_stubs.py").is_file():
    sys.path.append(str(HERE.parents[3] / "mods" / "perso" / "apex_probe" / "source"))

import sdk_stubs  # noqa: E402

# As unrealsdk.hooks.Block, set by install(): returned by a pre-hook, the game's function does not run.
BLOCK: Any = None


class FakeOption:
    """As mods_base's options: a value, its bounds (a slider) or choices (a spinner), what the menu shows; setting the
    value runs on_change_anytime, then on_change_while_enabled while its mod is enabled, before the value changes. As
    mods_base's guard (options.py, ValueOption.__setattr__), a value set during those runs is a plain set."""

    def __init__(self, identifier: str, value: Any, *bounds: Any, **kwargs: Any) -> None:
        self.on_change_anytime = self.on_change_while_enabled = None
        self.identifier, self.default_value, self.kwargs, self.mod = identifier, value, kwargs, None
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")
        self.step, self.is_integer = kwargs.get("step", 1), kwargs.get("is_integer", True)
        self.is_hidden = kwargs.get("is_hidden", False)
        self.min_value = self.max_value = None
        if len(bounds) == 1:
            self.choices = bounds[0]
        elif bounds:
            self.min_value, self.max_value = bounds
        self.value = value
        self.on_change_anytime = kwargs.get("on_change_anytime")
        self.on_change_while_enabled = kwargs.get("on_change_while_enabled")

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "value" and not hasattr(self, "_on_change_recursion_guard"):
            # No try: as mods_base, a change that raises leaves the guard, and the option's changes stop running.
            super().__setattr__("_on_change_recursion_guard", True)
            if getattr(self, "on_change_anytime", None) is not None:
                self.on_change_anytime(self, value)
            mod = getattr(self, "mod", None)
            if getattr(self, "on_change_while_enabled", None) is not None and mod is not None and mod.is_enabled:
                self.on_change_while_enabled(self, value)
            del self._on_change_recursion_guard
        super().__setattr__(name, value)


class FakeKeybindOption(FakeOption):
    """As mods_base's KeybindOption: from_keybind copies a change of the option onto the bind, not the reverse."""

    @classmethod
    def from_keybind(cls, bind: Any) -> Any:
        option = cls(bind.identifier, bind.key, display_name=bind.display_name, description=bind.description,
                     is_hidden=bind.is_hidden)
        option.default_value = bind.default_key
        option.on_change_anytime = lambda _option, key: setattr(bind, "key", key)
        return option


class FakeNestedOption:
    def __init__(self, identifier: str, children: list, **kwargs: Any) -> None:
        self.identifier, self.children = identifier, children
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")


class FakeKeybind:
    """As mods_base's keybind: a key the player may change, and the callback the SDK runs on its events."""

    def __init__(self, identifier: str, key: str | None, callback: Any, kwargs: dict) -> None:
        self.identifier, self.key, self.default_key, self.callback = identifier, key, key, callback
        self.kwargs = kwargs
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")
        self.is_hidden = kwargs.get("is_hidden", False)
        self.event_filter = kwargs.get("event_filter", "IE_Pressed")
        self.is_enabled = False

    def enable(self) -> None:
        self.is_enabled = True

    def disable(self) -> None:
        self.is_enabled = False


class FakeHook:
    """As mods_base's hook: the function, callable as it is, on the game's function only while enabled."""

    def __init__(self, fn: Any, path: str, kind: Any) -> None:
        self.fn, self.path, self.kind, self.enabled = fn, path, kind, False

    @property
    def is_enabled(self) -> bool:
        return self.enabled

    def __call__(self, *args: Any) -> Any:
        return self.fn(*args)

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False


class FakeMod:
    """As mods_base.Mod: its hooks and keys on before on_enable, off before on_disable; its settings file exists as
    state["settings_exists"] says, and a save fails while state["refuse_saves"]."""

    def __init__(self, state: dict, **kwargs: Any) -> None:
        self.state, self.kwargs, self.is_enabled = state, kwargs, False
        self.settings_file = types.SimpleNamespace(exists=lambda: state["settings_exists"])
        for option in kwargs.get("options") or []:
            option.mod = self

    def save_settings(self) -> None:
        if self.state["refuse_saves"]:
            raise OSError("disk full")
        self.state["settings_saves"] += 1

    def iter_display_options(self):
        yield from self.kwargs.get("options", ())

    def _switchables(self) -> list:
        return [*(self.kwargs.get("hooks") or []), *(self.kwargs.get("keybinds") or [])]

    def enable(self) -> None:
        self.is_enabled = True
        for item in self._switchables():
            item.enable()
        self.kwargs["on_enable"]()

    def disable(self) -> None:
        self.is_enabled = False
        for item in self._switchables():
            item.disable()
        self.kwargs["on_disable"]()


def install() -> dict:
    """The probes' fake SDK, with the SDK's own hooks (in state["raw_hooks"]) and weak pointers, and mods_base's
    options, keys, hooks and mod; the mods built are in state["mods"]."""
    global BLOCK
    state = sdk_stubs.install()
    state.update(mods=[], raw_hooks={}, settings_exists=True, settings_saves=0, refuse_saves=False)
    hooks, raw = sys.modules["unrealsdk.hooks"], state["raw_hooks"]
    hooks.add_hook = lambda path, kind, identifier, callback: raw.setdefault((path, kind, identifier), callback)
    hooks.has_hook = lambda path, kind, identifier: (path, kind, identifier) in raw
    hooks.remove_hook = lambda path, kind, identifier: raw.pop((path, kind, identifier), None) is not None
    BLOCK = hooks.Block
    # The game's objects live as long as the test keeps them.
    sys.modules["unrealsdk.unreal"].WeakPointer = lambda obj: (lambda: obj)
    mods_base = sys.modules["mods_base"]
    mods_base.BoolOption = mods_base.SliderOption = mods_base.SpinnerOption = FakeOption
    mods_base.KeybindOption = FakeKeybindOption
    mods_base.NestedOption = FakeNestedOption
    mods_base.hook = lambda path, kind=None, **_kwargs: (lambda fn: FakeHook(fn, path, kind))
    mods_base.keybind = lambda identifier, key=None, callback=None, **kwargs: FakeKeybind(
        identifier, key, callback, kwargs)
    # As mods_base: build_mod makes the class it is given, a subclass of Mod (the mod's family.FamilyMod).
    mods_base.Mod = FakeMod
    state["warnings"] = []
    sys.modules["unrealsdk.logging"].warning = lambda text: state["warnings"].append(text)

    def build_mod(cls: type = FakeMod, **kwargs: Any) -> FakeMod:
        state["mods"].append(cls(state, **kwargs))
        return state["mods"][-1]

    mods_base.build_mod = build_mod
    return state


def fresh_package() -> None:
    """Forgets the mod's modules, so that the next import builds the mod anew."""
    for name in [name for name in sys.modules if name == "apex_heirloom" or name.startswith("apex_heirloom.")]:
        del sys.modules[name]
