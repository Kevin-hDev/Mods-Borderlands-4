"""The game's resource pool library, faked: the reserve the grapple spends, and how it can fail.

Two test files drive apex_grapple.stamina through the same fake game; one copy keeps them describing
the same game.
"""

import types
from typing import Any

import unrealsdk

TYPE_HANDLE = 11
POOL = "Vault_Power"


class Handle:
    def __init__(self, kind: int, name: str) -> None:
        self.kind = kind
        self.name = name


class Library:
    """GameResourcePoolFunctionLibrary: one reserve, its maximum, and the amounts taken from it."""

    def __init__(self) -> None:
        self.value = 100.0
        self.maximum = 100.0
        self.taken: list[float] = []
        self.reads = 0
        self.failing = False

    def _check(self) -> None:
        if self.failing:
            raise RuntimeError("the game refused")

    def GetResourcePoolValue(self, _owner: Any, _handle: Handle) -> float:
        self._check()
        return self.value

    def GetResourcePoolPercent(self, _owner: Any, _handle: Handle) -> float:
        self._check()
        return self.value / self.maximum if self.maximum else 0.0

    def AdjustResourcePoolValue(self, _owner: Any, _handle: Handle, amount: float) -> None:
        self._check()
        self.taken.append(amount)
        self.value = max(0.0, min(self.maximum, self.value + amount))


LIBRARY = "GameResourcePoolFunctionLibrary"


def install(stamina: Any) -> Library:
    """Puts the fake library behind the mod's stamina module and counts the type lookups.

    Every other class keeps the fake SDK's own answer: the aim still finds the game's trace library.
    """
    library = Library()
    parameter = types.SimpleNamespace(TypeHandle=TYPE_HANDLE)
    reader = types.SimpleNamespace(_find=lambda _name: parameter)
    others = unrealsdk.find_class

    def find_class(name: str, **kwargs: Any) -> Any:
        if name != LIBRARY:
            return others(name, **kwargs)
        library.reads += 1
        return types.SimpleNamespace(ClassDefaultObject=library, _find=lambda _name: reader)

    unrealsdk.find_class = find_class
    unrealsdk.unreal.FGameDataHandle = Handle
    stamina.forget()
    return library
