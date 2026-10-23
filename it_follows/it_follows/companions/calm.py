"""Reinforcements, trial 175: a companion's staggers taken away for good, at the follow's start (decision 43, Kevin, 21
October 2026: « retiré totalement les sursaut des comapgnons et ca on sait deja le faire »).

It Follows' trial 89 (docs/RUN/enquetes/2026-10-18-essai-89-sursauts-bloques.md): LockHitReactions(AIActor, type,
reason, Block) on OakHitReactionBlueprintLibrary, called on living enemies without a crash; Kevin saw none of them
stagger after (verified in game, twice). Its type is an ELockedHitReaction (All 0, Flinch 1, Stagger 2, Launch 3,
Ragdoll 4, Melee 5, listed by trial 88). It Follows left it because Block=False was never shown to give the reactions
back; a companion never needs them back. Only Stagger and Launch were ever blocked in game; Flinch, the small jolt,
is blocked too here, never tried (non vérifié); Ragdoll, a fall that may be the death's own, is left alone. Never
called on a dead character.
"""

from typing import Any, Callable

import unrealsdk

LIBRARY = "OakHitReactionBlueprintLibrary"
ENUM = "ELockedHitReaction"
BLOCKED = ("Flinch", "Stagger", "Launch")
# ELockedHitReaction as trial 88 listed it, for when the SDK has no enum to hand (It Follows' trial 89 did the same).
VALUES = {"Flinch": 1, "Stagger": 2, "Launch": 3}
REASON = "RenfortsCompanion"


def kinds() -> dict[str, Any]:
    try:
        enum = unrealsdk.find_enum(ENUM)
        return {name: getattr(enum, name) for name in BLOCKED}
    except Exception:
        return dict(VALUES)


def calm(actor: Any, note: Callable[[str], None]) -> list[str] | str:
    """BLOCKED locked on a living companion, each call said first: the names locked, or "dead"."""
    try:
        if actor.HealthState.bCurrentlyDead is True:
            return "dead"
    except Exception:
        return "dead"
    library = unrealsdk.find_class(LIBRARY).ClassDefaultObject
    locked = []
    for name, kind in kinds().items():
        note(f"about to call LockHitReactions({name}) on {str(actor.Name)[:80]}")
        library.LockHitReactions(AIActor=actor, type=kind, reason=REASON, Block=True)
        locked.append(name)
    return locked
