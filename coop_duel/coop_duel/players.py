"""The players of the game, as the host sees them: his own character and each guest's, read from the game state's player
list. Only the host's game decides teams and damage for everyone (trial 6, docs/duel/enquetes/
2026-10-17-invite-sans-mods.md: a guest without any mod duels as well), so a game whose characters are not under its
authority is a guest's, and the duel is not started there.

Each character is the same object before and after a death (trial 2, verified in game): it is held by a WeakPointer
and found again at each beat, never kept as a raw reference.
"""

from itertools import islice
from typing import Any, NamedTuple

import mods_base
import unrealsdk

from . import report

# A game holds 4 players; the bound keeps a broken player list from running long inside a frame.
MAX_PLAYERS = 8
MAX_NAME = 24


class Found(NamedTuple):
    host: Any  # the host's character, None while he has none
    guests: list[Any]  # each guest's character on foot
    riding: int  # guests whose pawn is not on foot (a vehicle)
    host_on_foot: bool


def world() -> Any:
    """The world in play, None while the game has none."""
    try:
        return mods_base.ENGINE.GameViewport.World
    except Exception:
        return None


def label(pawn: Any) -> str:
    """The character's object name: what the log calls a player."""
    return report.shown(getattr(pawn, "Name", None))


def on_foot(pawn: Any) -> bool:
    """A character on foot has a CharacterMovement; a vehicle has none (trial 1)."""
    return bool(getattr(pawn, "CharacterMovement", None))


def find(world: Any) -> Found | None:
    """The host's character and his guests', None when this game is not the host's. Raises when the game state cannot
    be read: the caller decides what an unreadable game means."""
    authority = unrealsdk.find_enum("ENetRole").ROLE_Authority
    host, guests, riding, host_on_foot = None, [], 0, False
    for state in islice(world.GameState.PlayerArray, MAX_PLAYERS):
        pawn = state.PawnPrivate
        if not pawn:
            continue
        if pawn.GetLocalRole() != authority:
            return None
        if pawn.IsLocallyControlled():
            host, host_on_foot = pawn, on_foot(pawn)
        elif on_foot(pawn):
            guests.append(pawn)
        else:
            riding += 1
    return Found(host, guests, riding, host_on_foot)


def player_name(pawn: Any, fallback: str) -> str:
    """The name the game shows for this player, for the score on the screen only; fallback when it cannot be read.
    APlayerState.GetPlayerName is the engine's own reader: not verified in game in Borderlands 4."""
    try:
        name = str(pawn.PlayerState.GetPlayerName()).strip()
    except Exception:
        return fallback
    return name[:MAX_NAME] if name else fallback
