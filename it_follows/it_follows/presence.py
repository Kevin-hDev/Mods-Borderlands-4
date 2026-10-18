"""Whether a game is in play for It Follows, read as a run's start reads it (spec, section 2): the player's controller
and character, the vehicle being driven (the controller then holds no character, trial 9), and how many players the
game holds. Read only.

In co-op the host's game holds the enemies (docs/coop: the host decides where every character is, vérifié en jeu), so
the normal mode plays the enemies there, and a guest's plays only their speeds on its own copies (decision 129).
The host is the game whose own character has the authority, as Apex Movement's co-op tells it."""

from itertools import islice
from typing import Any, NamedTuple

import mods_base
import unrealsdk

from . import reads

# Borderlands 4 takes four players: the host and three guests.
MAX_GUESTS = 3
# The characters read to find them, as the census reads at most (census.MAX_SCAN).
MAX_SCAN = 400


class Seat(NamedTuple):
    """The controller, the character (None without one), and why there is no game to play in: None, no_character,
    in_vehicle or guest (a game of several players this one does not host)."""
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


def host(player: Any) -> bool:
    """Whether this game is the host's; a role that cannot be read is no host's."""
    try:
        return player.GetLocalRole() == unrealsdk.find_enum("ENetRole").ROLE_Authority
    except Exception:
        return False


def others(player: Any) -> list:
    """The other players' characters in this game, at most MAX_GUESTS: those holding a PlayerState, as trial 74
    found the guest's on the host (the guest's game names every character OakCharacter, its enemies too)."""
    found = []
    objects, _way = reads.search("OakCharacter", player)
    for actor in islice(objects, MAX_SCAN):
        if len(found) >= MAX_GUESTS:
            break
        name = reads.clean(getattr(actor, "Name", ""))
        if actor != player and not name.startswith("Default__") and getattr(actor, "PlayerState", None) is not None:
            found.append(actor)
    return found


def look() -> Seat:
    pc = mods_base.get_pc()
    player = getattr(pc, "OakCharacter", None) if pc is not None else None
    if player is None:
        return Seat(pc, None, "in_vehicle" if in_vehicle(pc) else "no_character")
    count = players()
    return Seat(pc, player, "guest" if count is not None and count > 1 and not host(player) else None)
