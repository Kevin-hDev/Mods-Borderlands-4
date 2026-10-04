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
