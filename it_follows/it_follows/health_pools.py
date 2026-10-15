"""An enemy's health pools where the game keeps them: the most each holds (an attribute) and what is left (a resource
pool). The one way It Follows reads and writes an enemy's health (decision 79).

Loveless Wyrms' way (its max_health.py and pools.py), verified in game on Vex's clones and Loveless's Wyrms (MV1,
releves/vie-des-invocations/2026-10-13-mv1-vie-doublee): SetAttributeToFloat writes the base of the maximum, which the
game's bonuses then multiply; GetValueOfAttribute reads the maximum, bonuses included; the pool keeps what it held, so
its share drops when its maximum grows, and AdjustResourcePoolValue gives it back. It Follows keeps its own copy
(decision 45: no mod leans on another). Not verified on the game's enemies.

An enemy has up to three pools, Resource_AI_Health_01 to 03 (health, shield, armor, in an order not read), each with
its maximum attribute (source unique: the game's decoded attributes, docs/candidats/editeur_de_sauvegarde/releves/
2026-10-01-niveau-max-suite). A pool the enemy lacks reads a maximum of zero or less: it is left alone.

The two libraries' class default objects and handles last as long as the game: built at the first use, dropped after
any failure and built again at the next.
"""

from typing import Any

import unrealsdk

POOLS = (("ai_health_resource_01_max_value", "Resource_AI_Health_01"),
         ("ai_health_resource_02_max_value", "Resource_AI_Health_02"),
         ("ai_health_resource_03_max_value", "Resource_AI_Health_03"))
ATTRIBUTES = "GbxAttributeBlueprintLibrary"
WRITER, WRITER_PARAMETER = "SetAttributeToFloat", "attribute"
RESOURCES = "GameResourcePoolFunctionLibrary"
POOL_READER, POOL_PARAMETER = "GetResourcePoolValue", "InResource"
UNREAD = -1.0
# A share this close is already the one asked: no call for the pool's rounding.
SHARE_NOISE = 0.001


class HealthPools:
    def __init__(self) -> None:
        self._attributes: Any = None
        self._resources: Any = None
        # Six at most, one by attribute and one by pool of POOLS: names from the code only.
        self._handles: dict[str, Any] = {}

    def most(self, actor: Any, pool: int) -> float:
        """The most pool can hold, the game's bonuses included; zero or less for a pool the enemy lacks."""
        attribute, _resource = POOLS[pool]
        return float(self._guarded(lambda: self._attribute_library().GetValueOfAttribute(attribute, actor, UNREAD)))

    def set_base(self, actor: Any, pool: int, base: float) -> float:
        """Writes the base of pool's maximum; the maximum read after it."""
        attribute, _resource = POOLS[pool]
        self._guarded(lambda: self._attribute_library().SetAttributeToFloat(
            self._handle(attribute, ATTRIBUTES, WRITER, WRITER_PARAMETER), actor, float(base)))
        return self.most(actor, pool)

    def share(self, actor: Any, pool: int) -> float:
        """What pool has left, from 0 to 1."""
        return float(self._pool_call("GetResourcePoolPercent", actor, pool))

    def set_share(self, actor: Any, pool: int, wanted: float) -> None:
        """Brings pool to wanted (0 to 1) of its maximum, raising it as well as lowering it (MV1 gave a doubled Wyrm
        back its full health). Nothing for a pool at zero, or already there."""
        left, now = float(self._pool_call(POOL_READER, actor, pool)), self.share(actor, pool)
        if now <= 0.0 or abs(now - wanted) <= SHARE_NOISE:
            return
        self._pool_call("AdjustResourcePoolValue", actor, pool, float(left / now * wanted - left))

    def forget(self) -> None:
        self._attributes = self._resources = None
        self._handles.clear()

    def _guarded(self, call: Any) -> Any:
        try:
            return call()
        except Exception:
            self.forget()
            raise

    def _attribute_library(self) -> Any:
        if self._attributes is None:
            self._attributes = unrealsdk.find_class(ATTRIBUTES).ClassDefaultObject
        return self._attributes

    def _handle(self, name: str, library: str, function: str, parameter: str) -> Any:
        if name not in self._handles:
            kind = int(unrealsdk.find_class(library)._find(function)._find(parameter).TypeHandle)
            self._handles[name] = unrealsdk.unreal.FGameDataHandle(kind, name)
        return self._handles[name]

    def _pool_call(self, function: str, actor: Any, pool: int, *extra: Any) -> Any:
        _attribute, resource = POOLS[pool]

        def call() -> Any:
            if self._resources is None:
                self._resources = unrealsdk.find_class(RESOURCES).ClassDefaultObject
            handle = self._handle(resource, RESOURCES, POOL_READER, POOL_PARAMETER)
            return getattr(self._resources, function)(actor, handle, *extra)

        return self._guarded(call)
