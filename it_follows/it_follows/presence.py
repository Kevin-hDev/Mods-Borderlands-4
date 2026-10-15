"""Whether a game is in play for It Follows, read as a run's start reads it (spec, section 2): the player's controller
and character, the vehicle being driven (the controller then holds no character, trial 9), and how many players the
game holds. Read only."""

from typing import Any, NamedTuple

import mods_base


class Seat(NamedTuple):
    """The controller, the character (None without one), and why there is no game to play in: None, no_character,
    in_vehicle or coop."""
    pc: Any
    player: Any
    why: str | None


def players() -> int | None:
    """How many players the game holds; None when it cannot be read."""
    try:
        return len(mods_base.ENGINE.GameViewport.World.GameState.PlayerArray)
    except Exception:
        return None


def in_vehicle(pc: Any) -> bool:
    """Whether the player drives: the controller's pawn is then the vehicle, a class of OakVehicle as the enemies aimed
    at in trial 6b."""
    try:
        return "Vehicle" in str(pc.Pawn.Class.Name)
    except Exception:
        return False


def look() -> Seat:
    pc = mods_base.get_pc()
    player = getattr(pc, "OakCharacter", None) if pc is not None else None
    if player is None:
        return Seat(pc, None, "in_vehicle" if in_vehicle(pc) else "no_character")
    count = players()
    return Seat(pc, player, "coop" if count is not None and count > 1 else None)
