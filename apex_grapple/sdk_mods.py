"""Test doubles for mod registration and input binding."""

import types
from typing import Any


class FakeOption:
    def __init__(self, identifier: str, value: Any, *args: Any, **kwargs: Any) -> None:
        self.on_change_anytime = None
        self.identifier, self.value, self.args = identifier, value, args
        self.display_name = kwargs.get("display_name", identifier)
        # mods_base's names for a slider's bounds; a switch has none.
        self.min_value, self.max_value = (args + (None, None))[:2]
        self.default_value = value
        self.mod = None
        self.is_hidden = kwargs.get("is_hidden", False)
        self.description = kwargs.get("description", "")
        self.step = kwargs.get("step", 1)
        self.is_integer = kwargs.get("is_integer", True)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "value" and getattr(self, "on_change_anytime", None) is not None:
            self.on_change_anytime(self, value)
        super().__setattr__(name, value)


class FakeNested:
    def __init__(self, identifier: str, children: list, **kwargs: Any) -> None:
        self.identifier, self.children = identifier, children
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")
        self.description_title = kwargs.get("description_title") or self.display_name
        self.mod = None
        self.is_hidden = kwargs.get("is_hidden", False)


class FakeButton:
    def __init__(self, identifier, **kwargs):
        self.identifier = identifier
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")
        self.on_press = kwargs.get("on_press")
        self.mod = None
        self.is_hidden = kwargs.get("is_hidden", False)


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
    """Behaves as mods_base.Mod does wherever this mod depends on it."""

    def __init__(self, state: dict, **kwargs: Any) -> None:
        self.state, self.kwargs = state, kwargs
        self.name = kwargs.get("name", "")
        self.is_enabled = False
        self.settings_file = types.SimpleNamespace(exists=lambda: state["settings_exists"])
        self.options = kwargs.get("options", [])
        self.saved = 0
        self.fail_save = False
        def associate(options):
            for option in options:
                option.mod = self
                associate(getattr(option, "children", []))
        associate(self.options)

    def save_settings(self):
        if self.fail_save:
            raise OSError("cannot save")
        self.saved += 1

    def iter_display_options(self):
        yield from self.options

    def enable(self) -> None:
        self.is_enabled = True
        for hook in self.kwargs.get("hooks", []):
            hook.enable()
        if self.kwargs.get("on_enable"):
            self.kwargs["on_enable"]()

    def disable(self) -> None:
        self.is_enabled = False
        for hook in self.kwargs.get("hooks", []):
            hook.disable()
        if self.kwargs.get("on_disable"):
            self.kwargs["on_disable"]()


class FakeKeybind:
    """Stands in for mods_base.keybind: tests fire key events by calling state["keybinds"][key]."""

    def __init__(self, state: dict, identifier: str, key: str, callback: Any) -> None:
        self.state, self.identifier, self.key, self.callback = state, identifier, key, callback

    def enable(self) -> None:
        self.state["keybinds"][self.key] = self.callback

    def disable(self) -> None:
        self.state["keybinds"].pop(self.key, None)
