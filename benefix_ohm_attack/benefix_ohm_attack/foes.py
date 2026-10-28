"""The foes around the player: the characters the beam may be thrown at, walked once a second at most.

Who is around is asked as the enemy probes ask it (mods/perso/apex_probe, verified in game in September 2026, and
by this mod's bounce on 2026-10-02): every character is an OakCharacter, found by walking the game's objects. That
walk costs about a frame, so it is bounded, made only when somebody asks, and once a second at most. The catch
(catch.py) and the bounce (bounce.py) both read this one list.

Each character is held weakly. Whether it is dead is read by who uses it, at that moment; whether it is a friend is
asked of the game once per character and per walk, and only for one about to be chosen.
"""

import math
from itertools import islice
from typing import Any

import unrealsdk
from unrealsdk import unreal

from . import aim, enemy, report

CHARACTER_CLASS = "OakCharacter"
# Bounded as the probes' walk is.
MAX_PAWNS = 400
# What the catch and the bounce look through at every frame: the nearest to the player.
MAX_FOES = 60
WALK_S = 1.0
# Frame times added up fall a hair short of the second they make.
ROUNDING_S = 1e-9


class Foe:
    """One character of the list: held weakly, with its species."""

    __slots__ = ("_held", "species", "_friend")

    def __init__(self, actor: Any, species: str) -> None:
        self._held = unreal.WeakPointer(actor)
        self.species = species
        self._friend: bool | None = None

    def actor(self) -> Any:
        """The character, or None once it has left the world."""
        return self._held()

    def friend(self, character: Any) -> bool:
        if self._friend is None:
            actor = self.actor()
            self._friend = actor is not None and enemy.friend(character, actor)
        return self._friend


_known: list[Foe] = []
# Time since the last walk; a session's first asking walks at once.
_age_s = WALK_S
_refused = False


def restart() -> None:
    """Called when the mod is switched on: nobody is known, and a walk the game refused is tried again."""
    global _known, _age_s, _refused
    _known, _age_s, _refused = [], WALK_S, False


def tick(passed: float) -> None:
    """Called at every frame: the list grows older."""
    global _age_s
    _age_s = min(_age_s + passed, WALK_S)


def known() -> int:
    return len(_known)


def _walk(character: Any) -> list[Foe]:
    here = enemy.place(character)
    found = []
    for pawn in islice(unrealsdk.find_all(CHARACTER_CLASS, exact=False), MAX_PAWNS):
        try:
            if pawn == character:
                continue
            species = aim.species_of(pawn)
            where = enemy.place(pawn) if aim.is_enemy(species) else None
            if where is None or enemy.dead(pawn):
                continue
            found.append((math.dist(here, where) if here is not None else 0.0, Foe(pawn, species)))
        except Exception:
            # One character the game will not let be read: the others are still looked at.
            continue
    found.sort(key=lambda entry: entry[0])
    return [foe for _distance, foe in found[:MAX_FOES]]


def around(character: Any) -> list[Foe]:
    """The foes known, walked anew when the list is a second old; nobody, said once, when the game refuses."""
    global _known, _age_s, _refused
    if not _refused and _age_s >= WALK_S - ROUNDING_S:
        _age_s = 0.0
        try:
            _known = _walk(character)
        except Exception as error:
            _refused, _known = True, []
            report.error_once("foes:walk", f"the game's characters could not be walked, the beam catches nobody "
                                           f"beside the aim and does not bounce: {error!r}")
    return _known
