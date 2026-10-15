"""Fakes of the game for the tests of the enemies' health (health_pools, toughness): the two libraries health_pools.py
calls, over enemies whose pools each hold a base, a bonus the game multiplies it by, and what is left. As MV1 measured
on Vex's clones and Loveless's Wyrms (releves/vie-des-invocations/2026-10-13-mv1-vie-doublee): a write sets the base,
the maximum read is the base times the bonus, a raised maximum leaves what is left as it was, a lowered one pulls it
down to the maximum. A pool an enemy lacks reads the default asked, and holds nothing. Every call is recorded in
calls, in order. Imported after sdk_stubs.install(), as it_follows is.
"""

import sys
import types
from typing import Any

calls: list[tuple] = []
# The functions that raise when called, a test sets them.
refused: set[str] = set()


class Pool:
    def __init__(self, base: float, bonus: float = 1.0, share: float = 1.0) -> None:
        self.base, self.bonus = base, bonus
        self.left = base * bonus * share

    @property
    def most(self) -> float:
        return self.base * self.bonus


class Enemy:
    """An enemy with its three pools, None for one it lacks."""

    def __init__(self, name: str, *pools: Pool | None) -> None:
        self.Name = name
        self.pools = list(pools) + [None] * (3 - len(pools))


def _pool(actor: Any, name: str) -> Pool | None:
    """The pool an attribute or a resource names: its number is the last two digits before _max_value or at the end.
    An enemy of another fake, made without pools, has none."""
    digits = name.removesuffix("_max_value")[-2:]
    pools = getattr(actor, "pools", None)
    return pools[int(digits) - 1] if pools is not None else None


def _record(function: str, *args: Any) -> None:
    calls.append((function, *args))
    if function in refused:
        raise RuntimeError(f"{function} refused")


class Attributes:
    def GetValueOfAttribute(self, attribute: str, actor: Enemy, default: float) -> float:
        _record("GetValueOfAttribute", attribute, actor.Name)
        pool = _pool(actor, attribute)
        return pool.most if pool is not None else default

    def SetAttributeToFloat(self, handle: Any, actor: Enemy, value: float) -> None:
        _record("SetAttributeToFloat", handle.name, actor.Name, round(value, 3))
        pool = _pool(actor, handle.name)
        if pool is not None:
            pool.base = value
            pool.left = min(pool.left, pool.most)


class Resources:
    def GetResourcePoolValue(self, actor: Enemy, handle: Any) -> float:
        _record("GetResourcePoolValue", handle.name, actor.Name)
        pool = _pool(actor, handle.name)
        return pool.left if pool is not None else 0.0

    def GetResourcePoolPercent(self, actor: Enemy, handle: Any) -> float:
        _record("GetResourcePoolPercent", handle.name, actor.Name)
        pool = _pool(actor, handle.name)
        return pool.left / pool.most if pool is not None and pool.most > 0.0 else 0.0

    def AdjustResourcePoolValue(self, actor: Enemy, handle: Any, amount: float) -> None:
        _record("AdjustResourcePoolValue", handle.name, actor.Name, round(amount, 3))
        pool = _pool(actor, handle.name)
        if pool is not None:
            pool.left = min(max(pool.left + amount, 0.0), pool.most)


class Library:
    """A game class reached by its class default object, whose functions' parameters give a definition kind."""

    def __init__(self, name: str, default: Any) -> None:
        self.name, self.default = name, default

    @property
    def ClassDefaultObject(self) -> Any:
        _record("ClassDefaultObject", self.name)
        return self.default

    def _find(self, function: str) -> Any:
        _record("_find", self.name, function)
        return types.SimpleNamespace(_find=lambda parameter: types.SimpleNamespace(TypeHandle=7))


def install(state: dict) -> None:
    """The two libraries in the fake SDK's classes, and the game's handle: its kind and the name it was made with."""
    state["classes"]["GbxAttributeBlueprintLibrary"] = Library("GbxAttributeBlueprintLibrary", Attributes())
    state["classes"]["GameResourcePoolFunctionLibrary"] = Library("GameResourcePoolFunctionLibrary", Resources())
    sys.modules["unrealsdk"].unreal.FGameDataHandle = lambda kind, name: types.SimpleNamespace(kind=kind, name=name)


def of(function: str) -> list[tuple]:
    return [call for call in calls if call[0] == function]
