"""The game's attribute library as Vehicle Driving's test SDK plays it: the vehicle guns' damage formula, one
definition for the whole game, handed back resolved in AddModifierToGbxAttribute's answer as on 2026-10-14."""

import enum
import types
from typing import Any

LIBRARY = "/Script/GbxEngine.GbxAttributeBlueprintLibrary"
ATTRIBUTE_DEF = types.SimpleNamespace(Name="GbxAttributeDef")
Kinds = enum.Enum("EGbxAttributeModifierType", ["PreAdd", "PostAdd", "OverrideBaseValue"])
Outcomes = enum.Enum("EGbxAttributeModifierActionExecOutput", ["failure", "EGbxAttributeModifierActionExecOutput_MAX"])


class DefPtr:
    """As the SDK's FGbxDefPtr: built in Python it is a name and a type, resolved nowhere (address 0)."""

    def __init__(self, name: str, kind: Any = None) -> None:
        self._name, self._type = name, kind

    def _get_address(self) -> int:
        return 0


class Definition(DefPtr):
    """The game's one definition of the formula: a balance formula whose Scalar is a constant."""

    def __init__(self, name: str) -> None:
        super().__init__(name, ATTRIBUTE_DEF)
        self.Value = types.SimpleNamespace(Scalar=types.SimpleNamespace(constant=1.0))

    def _get_address(self) -> int:
        return 0x7FF4C69B19E8


class _Attribute:
    """AddModifierToGbxAttribute's attribute parameter: its definition type, unless the test takes it away."""

    def __init__(self, library: "Library") -> None:
        self._library = library

    @property
    def Struct(self) -> Any:
        return ATTRIBUTE_DEF if self._library.typed else None


class Library:
    """AddModifierToGbxAttribute answers its handle, the attribute resolved, and its outcome as a number; every call
    is kept for the tests. `typed` False plays a parameter without its definition type, `resolves` False an answer
    without the definition."""

    def __init__(self) -> None:
        self.definition = Definition("calc_vehicle_weapon_damage")
        self.calls: list[tuple] = []
        self.modifiers: dict[int, tuple] = {}
        self.typed = True
        self.resolves = True
        adder = types.SimpleNamespace(_find=lambda name: _Attribute(self))
        self.cls = types.SimpleNamespace(_find=lambda name: adder, ClassDefaultObject=self)

    def AddModifierToGbxAttribute(self, pointer: DefPtr, context: Any, kind: Any, value: float, refresh: bool,
                                  outcome: Any) -> tuple:
        self.calls.append(("add", pointer._name, getattr(pointer._type, "Name", None), context, kind.name, value))
        handle = types.SimpleNamespace(Id=len(self.calls))
        self.modifiers[handle.Id] = (pointer._name, value)
        answer = self.definition if self.resolves and pointer._name == self.definition._name else DefPtr(pointer._name)
        return handle, answer, 0

    def RemoveAttributeModifier(self, handle: Any) -> bool:
        self.calls.append(("remove", handle.Id))
        return self.modifiers.pop(handle.Id, None) is not None


def enums(name: str) -> Any:
    return {Kinds.__name__: Kinds, Outcomes.__name__: Outcomes}[name]
