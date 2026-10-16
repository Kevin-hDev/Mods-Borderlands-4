"""Who killed an enemy the census reads dead, for the Hardcore (decision 89): Kevin, 15 October 2026, « il ne doit
compter que les ennemies tuer par le joueur, pas par le reste », Vex's spectres and Loveless's Wyrms among the rest.

Two fields of the dead character, read as values, never a call (a dead body is the game's to reuse): the game's
OakCharacter.KillerActor, and the engine's Pawn.LastHitBy, the controller that last hit it. Both are named in the
game's map of fields (releves/jeu/2026-09-23-carte-des-champs); what they hold after a death is not verified in game:
trial 31 writes down what each says. KillerActor read None on a living spectre (releves/spectres-vex/2026-10-11-p1b).

Each says player (the player's character, or the controller for LastHitBy), vehicle (what the controller drives),
none, unreadable, or the class of what it holds. A kill is the player's when KillerActor says player or vehicle, or
says none while LastHitBy says player.
"""

from typing import Any

from . import reads

PLAYER, VEHICLE, NONE, UNREADABLE = "player", "vehicle", "none", "unreadable"
MAX_CLASS_TEXT = 40
MAX_NAME_TEXT = 60


def _who(target: Any, player: Any, pc: Any) -> str:
    if target is None:
        return NONE
    if target == player or (pc is not None and target == pc):
        return PLAYER
    try:
        kind = str(target.Class.Name)[:MAX_CLASS_TEXT]
    except Exception:
        return "other:?"
    try:
        driven = pc is not None and target == pc.Pawn
    except Exception:
        driven = False
    return VEHICLE if driven else f"other:{kind}"


def _read(actor: Any, field: str, player: Any, pc: Any) -> str:
    try:
        target = getattr(actor, field)
    except Exception:
        return UNREADABLE
    return _who(target, player, pc)


def killed_by(actor: Any, player: Any, pc: Any) -> tuple[str, str]:
    """What KillerActor and LastHitBy say of a dead character."""
    return _read(actor, "KillerActor", player, pc), _read(actor, "LastHitBy", player, pc)


def killer_name(actor: Any) -> str:
    """The name of what KillerActor holds, a field of the dead character and one of the killer, never a call: which
    enemy killed another (trial 52: in Predator, 11 enemies killed by another character, with the one team on)."""
    try:
        target = actor.KillerActor
        return NONE if target is None else reads.clean(target.Name)[:MAX_NAME_TEXT]
    except Exception:
        return UNREADABLE


def by_player(said: tuple[str, str]) -> bool:
    killer, last_hit = said
    return killer in (PLAYER, VEHICLE) or (killer == NONE and last_hit == PLAYER)
