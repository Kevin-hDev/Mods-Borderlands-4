"""Fake UMG widgets for the window's tests: every Set* call recorded, children kept, a CheckBox's checked state kept
as the game does, and any other engine field answered with a structure that grows as it is read."""

from typing import Any

import unrealsdk


class Struct:
    def __getattr__(self, name: str) -> Any:
        if name.startswith("__"):
            raise AttributeError(name)
        value = Struct()
        setattr(self, name, value)
        return value


class Widget:
    created: list = []

    def __init__(self, kind: str, owner: Any) -> None:
        self.kind, self.owner = kind, owner
        self.children, self.slots, self.calls = [], [], {}
        self.checked = False
        self.Font = Struct()
        self.created.append(self)

    def IsChecked(self) -> bool:
        return self.checked

    def __getattr__(self, name: str) -> Any:
        if name.startswith("Set") or name.startswith("AddChild"):
            return lambda *args: self.call(name, args)
        if name[:1].isupper():
            value = Struct()
            setattr(self, name, value)
            return value
        raise AttributeError(name)

    def call(self, name: str, args: tuple) -> Any:
        if name == "SetContent":
            self.children[:] = [args[0]]
        elif name.startswith("AddChild"):
            self.children.append(args[0])
            slot = Widget("Slot", self)
            self.slots.append(slot)
            return slot
        elif name == "SetIsChecked":
            self.checked = bool(args[0])
        self.calls[name] = args
        return None


def install() -> None:
    """Every widget the window makes is one of these."""
    unrealsdk.construct_object = Widget


def text(widgets: dict, name: str) -> str:
    return widgets[name].calls["SetText"][0]
