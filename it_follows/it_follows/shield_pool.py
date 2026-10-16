"""An enemy's shield as It Follows gives it: the one way the mod adds, sizes, refills and takes off a blue bar
(decisions 111 to 113). The game's own way, which its trait Trait_Health_AddEnergyBar takes (its imports, trial 46):
DamageStatics.AddHealthPool with the shield's type; sized and filled through health_pools.py, as the BUFF writes health;
refilled over a time by RefillHealthPercentOvertime; taken off by RemoveHealthPool.

Trials 47 and 48 (docs/RUN/enquetes/2026-10-16-essai-47-bouclier-ajoute.md, vérifié en jeu on two bandits and a
Splice, no crash): the bar shows above the health and takes the shots first; the game sizes it as it pleases (100 % of
a bandit's health, 56 % of a Psycho Badass's), and the size written holds; it never refills by itself (its two
regeneration attributes read 0); a refill fills it over the time asked (12.8 % a second for 13 asked); taken off, its
layer and its pool are gone and the health is untouched.

The game picks the pool (bChoosePoolAutomatically, the pool 02 on the bandits): the shield's is the one whose maximum
read nothing before and something after. When that is not one pool, nothing more is written nor taken off: taking a
shield off names its pool, and a pool guessed could be the enemy's own armour (a boss's three bars). Never seen in
game.

The library's class default object and handles last as long as the game: built at the first use, dropped after any
failure and built again at the next.
"""

from typing import Any

import unrealsdk

from . import health_pools

SHIELD = "HealthType_AI_Energy"
# The pools' own names, as AddHealthPool and RemoveHealthPool want them: the resources' of health_pools.POOLS.
POOLS = ("ResourcePool_AI_Health_01", "ResourcePool_AI_Health_02", "ResourcePool_AI_Health_03")
DAMAGE = "DamageStatics"
# The pool named to AddHealthPool, which chooses its own: the bandits' (trial 47).
ASKED = 1
# Every tenth of a second, as trial 47's refill.
REFILL_TICK_S = 0.1
# The size written is reached within 1 %, as toughness.py's.
TOLERANCE = 0.01
TYPES_MOST = 6


def shielded(actor: Any) -> bool:
    """Whether the enemy already holds a shield of the game's type, by its health types: a field read."""
    slots = list(actor.HealthState.HealthTypeStates)[:TYPES_MOST]
    return SHIELD in [str(getattr(slot.HealthType, "_name", "")) for slot in slots]


class ShieldPool:
    def __init__(self, pools: Any = None) -> None:
        self.pools = pools if pools is not None else health_pools.HealthPools()
        self._damage: Any = None
        # By (function, parameter, name): at most 3 functions, 2 parameters, 4 names, from the code only.
        self._handles: dict[tuple[str, str, str], Any] = {}

    def add(self, actor: Any, share: float) -> tuple[int, float] | None:
        """A shield of share of the health the enemy holds, full: its pool and the maximum read; None when no single
        new pool was read."""
        before = [self.pools.most(actor, pool) for pool in range(len(POOLS))]
        self._guarded(lambda: self._library().AddHealthPool(
            Context=actor, HealthType=self._handle("AddHealthPool", "HealthType", SHIELD), Segments=[],
            bChoosePoolAutomatically=True, Pool=self._handle("AddHealthPool", "Pool", POOLS[ASKED]),
            bRefillAllHealth=False, RefillPercent=1.0))
        new = [pool for pool in range(len(POOLS)) if before[pool] <= 0.0 < self.pools.most(actor, pool)]
        if len(new) != 1:
            return None
        pool = new[0]
        target = share * sum(most for most in before if most > 0.0)
        got = self.pools.set_base(actor, pool, target)
        if got > 0.0 and abs(got - target) > TOLERANCE * target:
            got = self.pools.set_base(actor, pool, target * target / got)
        self.pools.set_share(actor, pool, 1.0)
        return pool, got

    def fill(self, actor: Any, pool: int) -> float:
        return self.pools.share(actor, pool)

    def most(self, actor: Any, pool: int) -> float:
        return self.pools.most(actor, pool)

    def refill(self, actor: Any, seconds: float) -> None:
        """The whole shield filled again over seconds, whatever hits it meanwhile."""
        self._guarded(lambda: self._library().RefillHealthPercentOvertime(
            Context=actor, HealthType=self._handle("RefillHealthPercentOvertime", "HealthType", SHIELD), Percent=1.0,
            MaxPercent=1.0, Duration=float(seconds), TickRate=REFILL_TICK_S))

    def remove(self, actor: Any, pool: int) -> bool:
        return bool(self._guarded(lambda: self._library().RemoveHealthPool(
            Context=actor, HealthType=self._handle("RemoveHealthPool", "HealthType", SHIELD),
            Pool=self._handle("RemoveHealthPool", "Pool", POOLS[pool]))))

    def forget(self) -> None:
        self._damage = None
        self._handles.clear()

    def _guarded(self, call: Any) -> Any:
        try:
            return call()
        except Exception:
            self.forget()
            raise

    def _library(self) -> Any:
        if self._damage is None:
            self._damage = unrealsdk.find_class(DAMAGE).ClassDefaultObject
        return self._damage

    def _handle(self, function: str, parameter: str, name: str) -> Any:
        """A handle of the type the function's parameter wants: a handle of another type is refused (apex_probe,
        apex_pool_handle.py)."""
        key = (function, parameter, name)
        if key not in self._handles:
            kind = int(unrealsdk.find_class(DAMAGE)._find(function)._find(parameter).TypeHandle)
            self._handles[key] = unrealsdk.unreal.FGameDataHandle(kind, name)
        return self._handles[key]
