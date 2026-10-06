"""Fake options and hook declarations used by the Vehicle Driving SDK fixture."""
from typing import Any


class FakeOption:
    def __init__(self, identifier: str, value: Any, *args: Any, **kwargs: Any) -> None:
        # args holds a slider's bounds, in mods_base's order: min_value, max_value.
        self.identifier, self.value, self.args, self.kwargs = identifier, value, args, kwargs
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")
        self.step = kwargs.get("step", 1)
        self.is_integer = kwargs.get("is_integer", True)
        self.min_value, self.max_value = (args + (None, None))[:2]
        self.default_value = value


class FakeSpinnerOption(FakeOption):
    """As mods_base's SpinnerOption: a value among its choices, the names the window shows."""

    def __init__(self, identifier: str, value: Any, choices: list, wrap_enabled: bool = False, **kwargs: Any) -> None:
        super().__init__(identifier, value, **kwargs)
        self.choices, self.wrap_enabled = list(choices), wrap_enabled


class FakeKeybindOption(FakeOption):
    """As mods_base's KeybindOption: made from a bind, whose key follows the option's value (from_keybind)."""

    @classmethod
    def from_keybind(cls, bind: Any) -> "FakeKeybindOption":
        option = cls(bind.identifier, bind.key, display_name=bind.display_name, description=bind.description)
        option.default_value = bind.default_key
        option.is_hidden = bind.is_hidden
        option.on_change_anytime = lambda _option, key: setattr(bind, "key", key)
        return option

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "value" and getattr(self, "on_change_anytime", None) is not None:
            self.on_change_anytime(self, value)
        super().__setattr__(name, value)


class FakeNestedOption:
    def __init__(self, identifier: str, children: list, **kwargs: Any) -> None:
        self.identifier, self.children = identifier, children
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")


class FakeKeybind:
    """As mods_base's KeybindType where this mod relies on it: an identifier, a key and the press callback."""

    def __init__(self, identifier: str, key: str | None, callback: Any, **kwargs: Any) -> None:
        self.identifier, self.key, self.default_key, self.callback, self.kwargs = (
            identifier, key, key, callback, kwargs)
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")
        self.is_hidden = kwargs.get("is_hidden", False)


class FakeHook:
    def __init__(self, fn: Any, path: str, kind: str, identifier: str) -> None:
        self.fn, self.path, self.kind, self.identifier, self.enabled = fn, path, kind, identifier, False

    def __call__(self, *args: Any) -> Any:
        return self.fn(*args)

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False
