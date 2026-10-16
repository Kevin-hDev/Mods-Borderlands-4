"""The normal mode's aim (decisions 114 and 115, Kevin, 16 October 2026): every enemy it meets shoots tighter and its
bullets reach a moving hunter more often, by the level's factors (levels.py).

How, trials 50 and 51 (docs/RUN/enquetes/, vérifié en jeu, one enemy each): an enemy's weapon carries its aim in its
fire behaviours (WeaponBehavior_Use), each its own, shared with no other enemy. aiaccuracy and aiminaccuracy are a
spread: ×5, the enemy dealt 4 times less damage; ×0.2, 1.5 times more. aiprojectilespeed is what counts against a
hunter on the move: ×2, some 5 times more damage. Each is a GbxAttributeFloat whose Value and BaseValue are both
written; the game kept them for the trials' 15 and 20 s. Field writes, no call.

A behaviour is held by its path name with the game's values: met again (the census reads each enemy alive every
EVERY_S, a new weapon or a body the game gave to the next enemy), one still holding the values written is left; in
one that does not, each field holding another value has it for the game's, each still holding the one written keeps
the game's known, so that nothing is ever multiplied twice. Given back when the enemy is let
go, dead too (the game may give its weapon to another enemy, which must not keep them), and only where the values
written are still there.
"""

from itertools import islice
from typing import Any, Callable

import unrealsdk

USE = "WeaponBehavior_Use"
SPREAD = ("aiaccuracy", "aiminaccuracy")
SPEED = "aiprojectilespeed"
# A float read back equals the one written within this: the game keeps them in 32 bits, some 1e-6 at 12.
SAME = 1e-4
# Trial 50's bandit held one slot with one fire behaviour: room for an enemy with more.
SLOTS_MOST = 4
BEHAVIOURS_MOST = 16
SUPERS_MOST = 16
# The behaviours held: 200 enemies at most (enemies.MOST), a few weapons each.
HELD_MOST = 2000
# The writes said in the log, the first of each game; the rest are only made (speed.DETAILED).
DETAILED = 20


def behaviours(actor: Any) -> list:
    """The fire behaviours of the weapons the enemy holds, read field by field."""
    found = []
    for slot in islice(actor.ActiveWeapons.Slots, SLOTS_MOST):
        weapon = slot.Weapon
        if weapon is None:
            continue
        for behaviour in islice(weapon.behaviors, BEHAVIOURS_MOST):
            if behaviour is not None and any(str(owner.Name) == USE
                                             for owner in islice(behaviour.Class._superfields(), SUPERS_MOST)):
                found.append(behaviour)
    return found


class Aim:
    """spread: the level's factor on the spread (below 1, tighter); speed: on the bullets' speed. announce(call, log,
    **fields) notes a write before it is made."""

    def __init__(self, announce: Callable[..., None], spread: float, speed: float) -> None:
        self.announce = announce
        self.factors = {**dict.fromkeys(SPREAD, spread), SPEED: speed}
        # By path name: its weak pointer, and the game's (Value, BaseValue) of each field.
        self.held: dict[str, tuple[Any, dict[str, tuple[float, float]]]] = {}
        self.by_enemy: dict[str, list[str]] = {}
        self.detailed = 0

    def give(self, name: str, actor: Any) -> str:
        """The level's aim on every fire behaviour of an enemy alive: "given" when one was written, "held" when all
        held it, "no_weapon", "full", or "failed:X"."""
        try:
            found = behaviours(actor)
            if not found:
                return "no_weapon"
            written = False
            paths = self.by_enemy.setdefault(name, [])
            for behaviour in found:
                path = str(behaviour._path_name())
                known = self.held[path][1] if path in self.held else {}
                if known and self._ours(behaviour, known):
                    continue
                if not known and len(self.held) >= HELD_MOST and not self._forget_gone():
                    return "full"
                game = {}
                for field in self.factors:
                    attribute = getattr(behaviour, field)
                    game[field] = (known[field] if field in known and self._kept(attribute, field, known[field][0])
                                   else (float(attribute.Value), float(attribute.BaseValue)))
                self.held[path] = (unrealsdk.unreal.WeakPointer(behaviour), game)
                if path not in paths:
                    paths.append(path)
                self.announce("WeaponAim", log=self.detailed < DETAILED, on=name, behaviour=path)
                self.detailed += 1
                self._write(behaviour, game, ours=True)
                written = True
        except Exception as error:
            return f"failed:{type(error).__name__}"
        return "given" if written else "held"

    def take_off(self, name: str) -> str:
        """The game's values back on the enemy's behaviours still holding the level's: "given_back", "not_given", or
        "left" when none still held them (gone, or changed by the game)."""
        paths = self.by_enemy.pop(name, None)
        if not paths:
            return "not_given"
        back = False
        for path in paths:
            pointer, game = self.held.pop(path, (None, None))
            behaviour = pointer() if pointer is not None else None
            try:
                if behaviour is not None and self._ours(behaviour, game):
                    self.announce("WeaponAim", log=False, on=name, back=True)
                    self._write(behaviour, game, ours=False)
                    back = True
            except Exception as error:
                return f"failed:{type(error).__name__}"
        return "given_back" if back else "left"

    def _ours(self, behaviour: Any, game: dict[str, tuple[float, float]]) -> bool:
        return all(self._kept(getattr(behaviour, field), field, game[field][0]) for field in self.factors)

    def _kept(self, attribute: Any, field: str, value: float) -> bool:
        """Whether the field still holds the game's value times the level's factor."""
        return abs(float(attribute.Value) - value * self.factors[field]) <= SAME

    def _write(self, behaviour: Any, game: dict[str, tuple[float, float]], ours: bool) -> None:
        for field, factor in self.factors.items():
            attribute = getattr(behaviour, field)
            value, base = game[field]
            times = factor if ours else 1.0
            attribute.Value, attribute.BaseValue = value * times, base * times
            setattr(behaviour, field, attribute)

    def _forget_gone(self) -> bool:
        """The behaviours the game freed forgotten; whether there is room now."""
        for path in [path for path, (pointer, _) in self.held.items() if pointer() is None]:
            del self.held[path]
        return len(self.held) < HELD_MOST
