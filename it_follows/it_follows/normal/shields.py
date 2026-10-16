"""The normal mode's shields (decisions 111 to 113, Kevin, 16 October 2026): every enemy it meets without a shield,
bosses too (« Oui, eux aussi »), gets one of levels.SHIELD_SHARE of its health, at Bandit while the player keeps the
option, at Senior and Predator always. Only Predator's comes back: broken, levels.SHIELD_REFILL_AFTER_S later it fills
again at levels.SHIELD_REFILL_RATE a second, even under fire (Kevin: « c'est le meme fonctionnement que pour les 6
chasseur de l'arche »); one broken again during its refill waits for the refill's end. The game's shields are never
touched.

Every shield given is taken off the living when the mode stops or the game is left (decision 113: « Retirés tout de
suite »). A dead enemy is never called on: the game gives its body to the next one (spec, « Oublier les morts »); one
the census no longer reads is not either. Both are remembered by name, the pool and the maximum given: an enemy met
under that name still holding a shield of that maximum is the one given, taken back as such, never given a second; one
whose shield differs is the game's.
"""

from dataclasses import dataclass
from typing import Any, Callable

from .. import shield_pool
from . import levels

# A fill at or under this is broken (trial 46: an empty layer reads 0.0).
BROKEN = 0.001
# A shield read within this of the maximum given is the one given.
KEPT = 1e-4
# The enemies holding a shield given: the normal mode holds 200 at most (enemies.MOST), with room.
GIVEN_MOST = 240
# The bodies left with a shield, the oldest forgotten first: what some minutes of fights kill.
LEFT_MOST = 1000


@dataclass
class Given:
    pool: int
    most: float
    broken_at: float | None = None
    refilled_until: float | None = None


class Shields:
    """refill: whether a broken shield comes back (Predator). announce(call, log, **fields) notes a call before it is
    made."""

    def __init__(self, announce: Callable[..., None], refill: bool, pool: Any = None) -> None:
        self.announce, self.refill = announce, refill
        self.pool = pool if pool is not None else shield_pool.ShieldPool()
        self.given: dict[str, Given] = {}
        # By name, kept across the mode's games: a body left in one may be met in the next.
        self.left: dict[str, Given] = _left

    def give(self, name: str, actor: Any) -> str:
        """A shield given to an enemy alive without one; how it went."""
        if name in self.given:
            return "held"
        left = self.left.pop(name, None)
        try:
            if shield_pool.shielded(actor):
                if left is not None and abs(self.pool.most(actor, left.pool) - left.most) <= KEPT * left.most:
                    self.given[name] = Given(left.pool, left.most)
                    return "taken_back"
                return "had_one"
            if len(self.given) >= GIVEN_MOST:
                return "refused"
            self.announce("AddHealthPool", log=False, on=name)
            added = self.pool.add(actor, levels.SHIELD_SHARE)
        except Exception as error:
            return f"failed:{type(error).__name__}"
        if added is None:
            return "no_pool"
        self.given[name] = Given(*added)
        return "given"

    def keep(self, name: str, actor: Any, now: float) -> str | None:
        """Predator's: a shield broken refilled REFILL_AFTER_S later, once at a time. On an enemy alive only."""
        given = self.given.get(name)
        if not self.refill or given is None:
            return None
        if given.refilled_until is not None:
            if now < given.refilled_until:
                return None
            given.refilled_until = None
        try:
            fill = self.pool.fill(actor, given.pool)
        except Exception as error:
            return f"failed:{type(error).__name__}"
        if fill > BROKEN:
            given.broken_at = None
            return None
        if given.broken_at is None:
            given.broken_at = now
            return "broken"
        if now - given.broken_at < levels.SHIELD_REFILL_AFTER_S:
            return None
        seconds = 1.0 / levels.SHIELD_REFILL_RATE
        self.announce("RefillHealthPercentOvertime", log=False, on=name)
        try:
            self.pool.refill(actor, seconds)
        except Exception as error:
            given.broken_at = None
            return f"failed:{type(error).__name__}"
        given.broken_at, given.refilled_until = None, now + seconds
        return "refilled"

    def take_off(self, name: str, actor: Any, alive: bool) -> str:
        """The shield given taken off an enemy alive; one dead or away only remembered. The enemy is forgotten."""
        given = self.given.pop(name, None)
        if given is None:
            return "none"
        if not alive or actor is None:
            self.left.pop(name, None)
            self.left[name] = Given(given.pool, given.most)
            while len(self.left) > LEFT_MOST:
                del self.left[next(iter(self.left))]
            return "left"
        self.announce("RemoveHealthPool", log=False, on=name)
        try:
            return "removed" if self.pool.remove(actor, given.pool) else "not_removed"
        except Exception as error:
            return f"failed:{type(error).__name__}"


_left: dict[str, Given] = {}
