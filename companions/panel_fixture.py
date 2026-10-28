"""Fake UMG widgets for the window's tests: every Set* call recorded, children kept, a CheckBox's checked state kept as
the game does, and any other engine field answered with a structure that grows as it is read. Taken from It Follows'
panel_fixture.py (itself BL4 Arena's): each mod's tests keep their own, and Companions' never read It Follows'
files. Installed after sdk_stubs: the window's widgets made
by unrealsdk.construct_object, its enums read as "Enum.member"."""

from types import SimpleNamespace
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

    def __init__(self, kind: str, owner: Any = None) -> None:
        self.kind, self.owner = kind, owner
        self.children, self.slots, self.calls = [], [], {}
        self.checked = False
        self.selecting = False
        self.Font = Struct()
        self.created.append(self)

    def IsChecked(self) -> bool:
        return self.checked

    def GetIsSelectingKey(self) -> bool:
        """A key selector waiting for a key: what a test made it."""
        return self.selecting

    def GetValue(self) -> float:
        return self.calls.get("SetValue", (0.0,))[0]

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
            args[0].Slot = slot
            return slot
        elif name == "SetIsChecked":
            self.checked = bool(args[0])
        elif name == "SetSelectedKey":
            self.SelectedKey = args[0]
        self.calls[name] = args
        return None


class Enum:
    """An engine enum: each member read as "Enum.member"."""

    def __init__(self, name: str, **_options: Any) -> None:
        self.name = name

    def __getattr__(self, member: str) -> str:
        if member.startswith("__"):
            raise AttributeError(member)
        return f"{self.name}.{member}"


def install() -> None:
    unrealsdk.construct_object = lambda kind, outer=None, **_k: Widget(kind, outer)
    unrealsdk.find_enum = Enum
    unrealsdk.make_struct = lambda name, **fields: SimpleNamespace(struct=name, **fields)


def text(widgets: dict, name: str) -> str:
    return widgets[name].calls["SetText"][0]


def visible(widgets: dict, name: str) -> bool:
    return widgets[name].calls.get("SetVisibility", ("ESlateVisibility.Visible",))[0] in (
        "ESlateVisibility.Visible", "ESlateVisibility.SelfHitTestInvisible", "ESlateVisibility.HitTestInvisible")
