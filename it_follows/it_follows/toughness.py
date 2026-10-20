"""BUFF and BUFF+ on the enemies (decision 79): each enemy that joins the horde holds 20 % or 40 % more health, shield
and armor, keeping the share it had, and has the game's own maximum back once let go alive.

Kevin, 15 October 2026, between enemies that hold more and enemies that take less: « Vraie vie en plus », the damage
numbers unchanged. Each pool's maximum is raised to the game's own times the factor (health_pools.py): a first write
of the target shows the game's bonus over the base (MV1: 1.8 on a Spectre, 1.3 on a Wyrm), a second reaches the
target; the share from before is given back, since a pool keeps what it held. Trial 19: 40 of the game's enemies
read back 1.2 and 1.4 times their maximum, none failing. The bonus a kind showed is kept for the next of that kind,
whose first write then reaches the target; one whose bonus differs gets the second write all the same (audit of 16
October 2026: some 1 500 writes of trial 33's run, each with its read).

A killed enemy is never called on: the game reuses its body (spec, « Oublier les morts »), and acting on such a body
has crashed the game; nor is one the game took away alive (the horde's parked, the normal mode's lost from sight). Its
pools are remembered by name, with the game's own base of each: should the body be met again still holding the maximum
raised, that is said (health_kept_on_body) and the body is taken back as raised, the factor written from the game's
base, never laid twice: the audit of 15 October 2026 raised such an enemy of the normal mode ×1.69 in a script, where
×1.3 was meant. In trial 19 the one body found again read the game's own maximum for its level: the game sets a reused
body's health again (one case), and that body is raised as a new one. Normal touches nothing.

The normal mode's Hardcore changes the factor during a game (decision 89): harden sets the factor of the enemies met
next, and reach writes it on one enemy already raised, as the game's own base times it, its share kept: the game's
base is known since the first raise, and the maximum is that base times the game's bonus (MV1).

Every pool is raised, a Vile's eridium shield too: its two layers of HealthType_AI_Corruption (the pools 02 and 03 by
the types' order, not read), raised ×1.87 at Senior, still broke; 14 Vile met, all killed (20 October 2026, vérifié
en jeu). The lines written down say each enemy's health types.
"""

from typing import Any, Callable

from . import health_pools

# Within 1 % a maximum is reached: no bar shows less.
TOLERANCE = 0.01
# A factor this near 1 is Normal.
SAME = 1e-3
# A body that kept its raised maximum reads it back as written. Trial 19: an enemy's maximum grows 9.7 % a level, and
# a bat two levels up held by nature a maximum 0.3 % from one BUFF raised (1.2 against 1.097²), said kept within 1 %.
KEPT = 1e-4
# The horde holds 120 at most (horde.CROWD_MAX), each let go before it leaves: twice that is a fault, refused.
TENDED_MOST = 240
# The enemies whose pools are written down one by one, for a trial to read; the rest are counted.
DETAILED = 20
# The bodies left raised that are remembered, the oldest forgotten first: what a long run kills in some minutes.
LEFT_MOST = 1000
# The bonuses kept by kind and pool: three pools for each of the game's some 300 kinds of enemies, with room.
BONUS_MOST = 1024
# Kept across runs: a body killed in one run may be reused in the next. By name: its pools as tended.
_left: dict[str, list[tuple[int, float, float]]] = {}


class Toughness:
    """The enemies whose pools were raised by factor, each pool with the game's own base; announce(call, log,
    **fields) notes a call before it happens, note(event, **fields) writes a line."""

    def __init__(self, announce: Callable[..., None], note: Callable[..., None], factor: float,
                 pools: Any = None) -> None:
        self.announce, self.note, self.factor = announce, note, factor
        self.pools = pools if pools is not None else health_pools.HealthPools()
        # By name: (pool, game's base, maximum raised) for each pool the enemy has.
        self.tended: dict[str, list[tuple[int, float, float]]] = {}
        self.detailed = 0
        # By (kind, pool): the game's bonus over the base last read, the maximum over the base written.
        self.bonus: dict[tuple[str, int], float] = {}

    def start(self, chasers: list) -> int:
        """Raises the pools of every enemy drawn; how many were raised. Normal writes nothing and says nothing."""
        if abs(self.factor - 1.0) <= SAME:
            return 0
        raised = 0
        for chaser in chasers:
            actor = chaser.actor()
            if actor is None or chaser.name in self.tended:
                continue
            if len(self.tended) >= TENDED_MOST:
                self.note("health_refused", on=chaser.name, tended=len(self.tended))
                continue
            raised += self._raise(chaser.name, actor, getattr(chaser, "kind", None))
        return raised

    def _raise(self, name: str, actor: Any, kind: str | None = None) -> int:
        left = _left.pop(name, None)
        if left is not None and self._still_raised(actor, left):
            return self._take_back(name, actor, left)
        self.announce("SetAttributeToFloat", on=name, health=self.factor)
        pools: list[tuple[int, float, float]] = []
        line: dict = {}
        try:
            for pool in range(len(health_pools.POOLS)):
                most = self.pools.most(actor, pool)
                if most <= 0.0:
                    continue
                share = self.pools.share(actor, pool)
                game_base, raised = self._reach(actor, pool, most, most * self.factor, kind)
                # Kept before the share is given back: a maximum raised is given back even if that call fails.
                pools.append((pool, game_base, raised))
                line[f"pool_{pool + 1}"] = [round(most), round(raised)]
                self.pools.set_share(actor, pool, min(share, 1.0))
        except Exception as error:
            line["failed"] = type(error).__name__
        if not line:
            line["pools"] = 0
        if pools:
            self.tended[name] = pools
        if self.detailed < DETAILED or "failed" in line:
            self.detailed += 1
            try:
                line["types"] = health_pools.types(actor)
            except Exception as error:
                line["types"] = f"unread:{type(error).__name__}"
            self.note("health_raised", on=name, **line)
        return 1 if pools and "failed" not in line else 0

    def _still_raised(self, actor: Any, left: list[tuple[int, float, float]]) -> bool:
        """Whether the body holds the first pool's maximum as It Follows left it raised: a maximum near it by nature, a
        level up, is not (trial 19)."""
        pool, _game_base, raised = left[0]
        try:
            return abs(self.pools.most(actor, pool) - raised) <= KEPT * raised
        except Exception:
            return False

    def _take_back(self, name: str, actor: Any, left: list[tuple[int, float, float]]) -> int:
        """A body still raised tended again, the factor of now written from the game's base of each pool."""
        self.note("health_kept_on_body", on=name, most=round(left[0][2]))
        self.tended[name] = left
        return 1 if self.reach(name, actor) == "reached" else 0

    def harden(self, factor: float) -> None:
        """The factor of the enemies raised from now on; those already raised are given it by reach."""
        self.factor = factor

    def reach(self, name: str, actor: Any) -> str:
        """The factor written on an enemy already raised, one alive: each pool's base the game's own times it, its
        share kept."""
        pools = self.tended.get(name)
        if pools is None:
            return "not_raised"
        self.announce("SetAttributeToFloat", log=False, on=name, health=self.factor)
        try:
            for index, (pool, game_base, _raised) in enumerate(pools):
                share = self.pools.share(actor, pool)
                pools[index] = (pool, game_base, self.pools.set_base(actor, pool, game_base * self.factor))
                self.pools.set_share(actor, pool, min(share, 1.0))
        except Exception as error:
            return f"failed:{type(error).__name__}"
        return "reached"

    def _reach(self, actor: Any, pool: int, most: float, target: float,
               kind: str | None = None) -> tuple[float, float]:
        """Writes the base so the maximum read is target, the bonus the kind showed before taken off first; the
        game's own base, and the maximum reached."""
        key = (kind, pool) if kind else None
        written = target / self.bonus.get(key, 1.0) if key is not None else target
        got = self.pools.set_base(actor, pool, written)
        if got <= 0.0:
            raise ValueError("maximum not read after a write")
        game_base = most * written / got
        if key is not None and (key in self.bonus or len(self.bonus) < BONUS_MOST):
            self.bonus[key] = got / written
        if abs(got - target) > TOLERANCE * target:
            got = self.pools.set_base(actor, pool, written * target / got)
        return game_base, got

    def put_back(self, name: str, actor: Any, body_reused: bool) -> str:
        """The game's own maximum written back on an enemy let go alive, its share kept; one killed or taken back is
        only remembered. The enemy is forgotten either way."""
        pools = self.tended.pop(name, None)
        if pools is None:
            return "not_raised"
        if body_reused:
            _left.pop(name, None)
            _left[name] = pools
            while len(_left) > LEFT_MOST:
                del _left[next(iter(_left))]
            return "left"
        if actor is None:
            return "unavailable"
        self.announce("SetAttributeToFloat", on=name, back=True)
        try:
            for pool, game_base, _raised in pools:
                share = self.pools.share(actor, pool)
                self.pools.set_base(actor, pool, game_base)
                self.pools.set_share(actor, pool, min(share, 1.0))
        except Exception as error:
            return f"failed:{type(error).__name__}"
        return "restored"
