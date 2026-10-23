"""The normal mode's shields (decisions 111 to 113, Kevin, 16 October 2026): every enemy it meets without a shield,
bosses too (« Oui, eux aussi »), gets one of levels.SHIELD_SHARE of its health, at Bandit while the player keeps the
option, at Senior, Predator and God always. Only Predator's and God's come back: broken, levels.SHIELD_REFILL_AFTER_S
later it fills again at levels.SHIELD_REFILL_RATE a second, even under fire (Kevin: « c'est le meme fonctionnement
que pour les 6 chasseur de l'arche »); one broken again during its refill waits for the refill's end. The game's
shields are never touched.

Every shield given is taken off the living when the mode stops or the game is left (decision 113: « Retirés tout de
suite »). A dead enemy is never called on: the game gives its body to the next one (spec, « Oublier les morts »); one
the census no longer reads is not either. Both are remembered by name, the pool and the maximum given: an enemy met
under that name still holding a shield of that maximum is the one given, taken back as such, never given a second; one
whose shield differs is the game's.

An enemy whose three pools are all taken gets none (shield_pool.py: a Vile's eridium shield stopped breaking, 20
October 2026), nor one whose pools read nothing yet. When the game is asked but no single new pool is read after
(no_pool), what it laid is not known and never taken off; met again, such an enemy reads as holding the game's own
shield (had_one). The first NOTED_MOST enemies without room or with no_pool are written down, a game, with their
health types and pools.
"""

from dataclasses import dataclass
from typing import Any, Callable

from ..characters import health_pools, shield_pool
from . import levels

# A fill at or under this is broken (trial 46: an empty layer reads 0.0).
BROKEN = 0.001
# A shield read within this of the maximum given is the one given.
KEPT = 1e-4
# The enemies holding a shield given: the normal mode holds 200 at most (enemies.MOST), with room.
GIVEN_MOST = 240
# The bodies left with a shield, the oldest forgotten first: what some minutes of fights kill.
LEFT_MOST = 1000
# The enemies without room or with no_pool written down one by one, a game: as toughness.py's DETAILED.
NOTED_MOST = 20


@dataclass
class Given:
    pool: int
    most: float
    broken_at: float | None = None
    refilled_until: float | None = None


class Shields:
    """refill: whether a broken shield comes back (Predator and God). announce(call, log, **fields) notes a call before
    it is made, note(event, **fields) writes a line."""

    def __init__(self, announce: Callable[..., None], refill: bool, pool: Any = None,
                 note: Callable[..., None] | None = None) -> None:
        self.announce, self.refill = announce, refill
        self.note = note if note is not None else (lambda event, **fields: None)
        self.pool = pool if pool is not None else shield_pool.ShieldPool()
        self.given: dict[str, Given] = {}
        self.noted = 0
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
            before = self.pool.maxima(actor)
            if not shield_pool.read(before):
                return "unread"
            if not shield_pool.room(before):
                self._write_down("normal_shield_no_room", name, types=_types(actor), pools=_rounded(before))
                return "no_room"
            kinds = _types(actor)
            self.announce("AddHealthPool", log=False, on=name)
            added = self.pool.add(actor, levels.SHIELD_SHARE, before)
        except Exception as error:
            return f"failed:{type(error).__name__}"
        if added is None:
            self._no_pool(name, actor, kinds, before)
            return "no_pool"
        self.given[name] = Given(*added)
        return "given"

    def _no_pool(self, name: str, actor: Any, kinds: list[str] | str, before: list[float]) -> None:
        """The game asked, but no single new pool read after: what it laid, if anything, is not known, so it is never
        taken off; the enemy is written down before and after, for a trial to tell where it went."""
        try:
            after: list[int] | str = _rounded(self.pool.maxima(actor))
        except Exception as error:
            after = f"unread:{type(error).__name__}"
        self._write_down("normal_shield_no_pool", name, types=kinds, pools=_rounded(before), types_after=_types(actor),
                         pools_after=after)

    def _write_down(self, event: str, name: str, **fields: Any) -> None:
        if self.noted >= NOTED_MOST:
            return
        self.noted += 1
        self.note(event, on=name, **fields)

    def keep(self, name: str, actor: Any, now: float) -> str | None:
        """Predator's and God's: a shield broken refilled REFILL_AFTER_S later, once at a time. On an enemy alive
        only."""
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


def _types(actor: Any) -> list[str] | str:
    """The enemy's health types for a line: a read that fails is said, never raised."""
    try:
        return health_pools.types(actor)
    except Exception as error:
        return f"unread:{type(error).__name__}"


def _rounded(maxima: list[float]) -> list[int]:
    return [round(most) for most in maxima]


_left: dict[str, Given] = {}
