"""Fakes of the game for the tests of the enemies' health (health_pools, toughness, shield_pool): the three libraries
they call, over enemies whose pools each hold a base, a bonus the game multiplies it by, and what is left. As MV1 measured
on Vex's clones and Loveless's Wyrms (releves/vie-des-invocations/2026-10-13-mv1-vie-doublee): a write sets the base,
the maximum read is the base times the bonus, a raised maximum leaves what is left as it was, a lowered one pulls it
down to the maximum. A pool an enemy lacks reads the default asked, and holds nothing. Every call is recorded in
calls, in order. Imported after sdk_stubs.install(), as it_follows is.

The shield, as trials 47 and 48 saw it: AddHealthPool puts a full pool of the enemy's first maximum in the first pool
it lacks (the game's own size, SHIELD_BONUS on its base) and the shield's type among its health types; RemoveHealthPool
takes both off; RefillHealthPercentOvertime is only recorded.
"""

import sys
import types
from typing import Any

calls: list[tuple] = []
# The functions that raise when called, a test sets them.
refused: set[str] = set()
SHIELD = "HealthType_AI_Energy"
# The game's bonus on an added shield's base: not 1, so that the size is written twice.
SHIELD_BONUS = 1.25


class Pool:
    def __init__(self, base: float, bonus: float = 1.0, share: float = 1.0) -> None:
        self.base, self.bonus = base, bonus
        self.left = base * bonus * share

    @property
    def most(self) -> float:
        return self.base * self.bonus


class Enemy:
    """An enemy with its three pools, None for one it lacks."""

    def __init__(self, name: str, *pools: Pool | None, kinds: tuple = ("HealthType_AI_Flesh",)) -> None:
        self.Name = name
        self.pools = list(pools) + [None] * (3 - len(pools))
        self.HealthState = types.SimpleNamespace(bCurrentlyDead=False, HealthTypeStates=[])
        for kind in kinds:
            give_type(self, kind)


def give_type(actor: Any, kind: str) -> None:
    actor.HealthState.HealthTypeStates.append(types.SimpleNamespace(HealthType=types.SimpleNamespace(_name=kind)))


def types_of(actor: Any) -> list[str]:
    return [slot.HealthType._name for slot in actor.HealthState.HealthTypeStates]


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


class Damage:
    def AddHealthPool(self, **kwargs: Any) -> int:
        actor = kwargs["Context"]
        _record("AddHealthPool", actor.Name, kwargs["HealthType"].name, kwargs["Pool"].name,
                kwargs["bChoosePoolAutomatically"], kwargs["bRefillAllHealth"], kwargs["RefillPercent"],
                kwargs["Segments"])
        free = [index for index, pool in enumerate(actor.pools) if pool is None]
        if free and kwargs["HealthType"].name == SHIELD:
            actor.pools[free[0]] = Pool(actor.pools[0].most / SHIELD_BONUS, bonus=SHIELD_BONUS)
            give_type(actor, SHIELD)
        return 1

    def RemoveHealthPool(self, **kwargs: Any) -> bool:
        actor = kwargs["Context"]
        _record("RemoveHealthPool", actor.Name, kwargs["HealthType"].name, kwargs["Pool"].name)
        actor.pools[int(kwargs["Pool"].name[-2:]) - 1] = None
        actor.HealthState.HealthTypeStates = [slot for slot in actor.HealthState.HealthTypeStates
                                              if slot.HealthType._name != kwargs["HealthType"].name]
        return True

    def RefillHealthPercentOvertime(self, **kwargs: Any) -> int:
        _record("RefillHealthPercentOvertime", kwargs["Context"].Name, kwargs["HealthType"].name, kwargs["Percent"],
                kwargs["MaxPercent"], round(kwargs["Duration"], 3), kwargs["TickRate"])
        return 1


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
    """The three libraries in the fake SDK's classes, and the game's handle: its kind and the name it was made with."""
    state["classes"]["GbxAttributeBlueprintLibrary"] = Library("GbxAttributeBlueprintLibrary", Attributes())
    state["classes"]["GameResourcePoolFunctionLibrary"] = Library("GameResourcePoolFunctionLibrary", Resources())
    state["classes"]["DamageStatics"] = Library("DamageStatics", Damage())
    sys.modules["unrealsdk"].unreal.FGameDataHandle = lambda kind, name: types.SimpleNamespace(kind=kind, name=name)


def of(function: str) -> list[tuple]:
    return [call for call in calls if call[0] == function]
