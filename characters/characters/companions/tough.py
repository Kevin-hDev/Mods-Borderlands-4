"""Reinforcements, trials 140 to 142, then 172: a companion's health and shield, written once at the follow's start.

Kevin, 20 October 2026, after trial 139: « lemmy est pas tres fort il meur super vite, les campagnon doivent avoir
beaucoup plus de vie que ca et un petit bouclier qi se recharge ». It Follows' own ways, its modules handed in: a
pool's maximum written as its toughness writes it (toughness.py: a first write shows the
game's bonus over the base, a second reaches the target; trial 19, 40 enemies read back their factor); the shield
added, sized and filled as its shield_pool.py does (trials 47 and 48: the bar shows above the health and takes the
shots first; it never refills by itself). Trials 140 to 171 gave each companion ten times its own health, no shield.

Trial 172 (decisions 35 and 37): every companion holds the same health, its level's times the hunter's most (decision
38), and a shield of a share of it which does not fill again once broken, but at God. Since trial 187 the level
is the one played, read at the follow's start, no longer God written in. Since decision 69, the times, the shield's
share and its wait are the ones the companion's mod gives (tuning.Tuning): a level, or settings. Their own health
varied 13-fold, and they all take the same damage (trial 171). A pool's health type is the one at its place in the
list It Follows' health_pools.types reads (trial 172: so for the six read, the shield sized in the pool its type
names). Every pool of another type than the shield's is health: they share the target as they shared the game's
health (Crankus held two of flesh, trial 172). A companion that holds a shield has it sized; any other gets one added,
then sized. Set, never multiplied: a follow started again writes the same values (trial 164's health raised twice is
gone). Nothing is written back at the end: the character is the trial's own, born for it.

Trial 177 (decisions 37 and 44): at God, a shield broken comes back its level's 45 s later (Kevin, 20 October 2026:
« 30% des ppoints de vie recharger toutes les 45 secondes quand shileds casser »), as It Follows' Predator shields do
(normal/shields.py, keep): it fills at REFILL_RATE a second, It Follows' own, even under fire; one broken again while
it fills waits for the fill's end before the wait starts again.

A share of 0 is no shield (decision 50: the card's shield off; decision 67: the setting at 0 %): none is added nor
sized; a shield the game gives the character itself is left as the game has it (Crankus holds one, trial 172).
Trial 190: 21 births of 41 read no health pool (no_pool) at the follow's start, never at trial 189; why is not known.
The pools' types and maxima read are said with it, and the follow tries again (follow.py).
Trial 177 saw the Abomination's shield end a fill at 0.93, out of a fight, its health unchanged: hit unseen, or a fill
stopped short. What each fill leaves is noted when it ends, and the first MOST_ENDS summed up at the end.
"""

from typing import Any, Callable

# It Follows' normal/levels.py SHIELD_REFILL_RATE: the whole shield in some 7.7 s.
REFILL_RATE = 0.13
POOLS = 3
# A pool read back within 1 % of its target holds it (it_follows/shield_pool.py, TOLERANCE).
TOLERANCE = 0.01
# A fill at or under this is broken (It Follows' normal/shields.py: an empty layer reads 0.0).
BROKEN = 0.001
# The fills' ends kept for the summary: one every 53 s at most, some twenty minutes of a follow.
MOST_ENDS = 24


class Tough:
    """One character's health and shield; pools and shields are It Follows' HealthPools and ShieldPool, kinds its
    health_pools.types and shield its shield_pool.SHIELD, a shield's type; note(text) says a write or a call before it
    is made."""

    def __init__(self, actor: Any, name: str, note: Callable[[str], None], pools: Any, shields: Any,
                 kinds: Callable[[Any], list], shield: str) -> None:
        self.actor, self.name, self.note = actor, name, note
        self.pools, self.shields, self.kinds, self.shield_type = pools, shields, kinds, shield
        self.shield: int | None = None
        self.refill_after_s: float | None = None
        self.broken_at: float | None = None
        self.filled_until: float | None = None
        self.refills = 0
        self.ends: list[float] = []

    def _set(self, actor: Any, pool: int, target: float) -> list | None:
        """Pool's maximum written to target and the pool filled: its maximum before and after; None for a pool it
        lacks."""
        most = self.pools.most(actor, pool)
        if most <= 0.0:
            return None
        self.note(f"about to write the maximum of pool {pool} on {self.name}: {round(target)}")
        got = self.pools.set_base(actor, pool, target)
        if got > 0.0 and abs(got - target) > TOLERANCE * target:
            got = self.pools.set_base(actor, pool, target * target / got)
        self.pools.set_share(actor, pool, 1.0)
        return [round(most), round(got)]

    def harden(self, hunter_most: Any, tuned: Any, times: float | None = None) -> dict:
        """Its health times hunter_most, the hunter's most health, by tuned (tuning.Tuning) or by times (lower in a
        trial that wants it so), shared by its health pools, then its shield of tuned's share unless that is 0,
        filled again after tuned's wait: what chose them and why, the hunter's, and each pool's maximum before and
        after. Nothing written when hunter_most is no number (hunter_health.py says why), nor without a health pool,
        said with the types and maxima read. A failing call raises."""
        self.refill_after_s = tuned.refill_after_s
        said = list(tuned.said)
        if not isinstance(hunter_most, float):
            return {"level": said, "hunter": hunter_most, "health": "not_written", "shield": "none"}
        actor = self.actor()
        kinds = list(self.kinds(actor))[:POOLS]
        maxima = [self.pools.most(actor, pool) for pool in range(len(kinds))]
        health = [pool for pool, most in enumerate(maxima) if most > 0.0 and kinds[pool] != self.shield_type]
        if not health:
            return {"level": said, "hunter": round(hunter_most), "health": "no_pool", "shield": "none",
                    "types": kinds, "maxima": [round(most) for most in maxima]}
        target, whole = (tuned.times if times is None else times) * hunter_most, sum(maxima[pool] for pool in health)
        written = {str(pool): self._set(actor, pool, target * maxima[pool] / whole) for pool in health}
        held = [pool for pool, most in enumerate(maxima) if most > 0.0 and kinds[pool] == self.shield_type]
        return {"level": said, "hunter": round(hunter_most), "health": written,
                "shield": self._shield(actor, tuned.shield, target, held) if tuned.shield > 0.0 else "off"}

    def _shield(self, actor: Any, share: float, target: float, held: list[int]) -> Any:
        if held:
            pool = held[0]
        else:
            self.note(f"about to call AddHealthPool on {self.name}")
            added = self.shields.add(actor, share)
            if added is None:
                return "no_single_pool"
            pool = added[0]
        sized = self._set(actor, pool, share * target)
        if sized is None:
            return "unsized"
        self.shield = pool
        return [pool, *sized]

    def keep(self, now: float) -> str | None:
        """Once a sample: what its shield holds, from 0 to 1, then ,broken the sample it is first read broken and
        ,refill when it is filled again; None without one. A failing read raises; a failing fill is said, and the
        wait starts again."""
        if self.shield is None:
            return None
        actor = self.actor()
        said = f"{float(self.shields.fill(actor, self.shield)):.2f}"
        if self.refill_after_s is None:
            return said
        if self.filled_until is not None:
            if now < self.filled_until:
                return said
            self.filled_until = None
            self.note(f"fill ended on {self.name}: {said}")
            if len(self.ends) < MOST_ENDS:
                self.ends.append(float(said))
        if float(said) > BROKEN:
            self.broken_at = None
            return said
        if self.broken_at is None:
            self.broken_at = now
            return f"{said},broken"
        if now - self.broken_at < self.refill_after_s:
            return said
        seconds = 1.0 / REFILL_RATE
        self.broken_at = None
        self.note(f"about to call RefillHealthPercentOvertime on {self.name}")
        try:
            self.shields.refill(actor, seconds)
        except Exception as error:
            return f"{said},refill_failed:{type(error).__name__}"
        self.filled_until = now + seconds
        self.refills += 1
        return f"{said},refill"

    def shield_share(self) -> float | None:
        """What its shield holds, from 0 to 1, read only (trial 178's bars); None without one, or unread."""
        if self.shield is None:
            return None
        try:
            return round(float(self.shields.fill(self.actor(), self.shield)), 3)
        except Exception:
            return None

    def health(self) -> float | None:
        """What its health pool (the first) holds, from 0 to 1; None when unread."""
        try:
            return round(float(self.pools.share(self.actor(), 0)), 2)
        except Exception:
            return None

    def layers(self) -> Any:
        """Its pools' maxima and its health types, read at the end: a layer the game added since the start shows
        (Crankus's second flesh, trial 172). Why when unread."""
        try:
            actor = self.actor()
            return {"most": [max(0, round(self.pools.most(actor, pool))) for pool in range(POOLS)],
                    "types": list(self.kinds(actor))[:POOLS + 1]}
        except Exception as error:
            return f"unread:{type(error).__name__}"
