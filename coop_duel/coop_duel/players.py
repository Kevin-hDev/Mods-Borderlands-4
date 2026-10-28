"""The players of the game, as the host sees them: his own character and each guest's, read from the game state's player
list (everyone). Only the host's game decides teams and damage for everyone (trial 6, docs/duel/enquetes/
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


class Player(NamedTuple):
    """One player of the game as the host reads him."""
    state: Any  # his PlayerState: who he is for the whole session, whatever his character does
    pawn: Any  # his character, the vehicle he drives or rides, None while he has none
    on_foot: bool
    host: bool


def world() -> Any:
    """The world in play, None while the game has none."""
    try:
        return mods_base.ENGINE.GameViewport.World
    except Exception:
        return None


def label(pawn: Any) -> str:
    """The character's object name, written beside a player's number J (report.player) to match a line with the
    game's own."""
    return report.shown(getattr(pawn, "Name", None))


def on_foot(pawn: Any) -> bool:
    """A character on foot has a CharacterMovement; a vehicle has none (trial 1)."""
    return bool(getattr(pawn, "CharacterMovement", None))


def everyone(world: Any) -> list[Player] | None:
    """Every player of the game, the host first, None when this game is not the host's. Raises when the game state
    cannot be read: the caller decides what an unreadable game means."""
    authority = unrealsdk.find_enum("ENetRole").ROLE_Authority
    found = []
    for state in islice(world.GameState.PlayerArray, MAX_PLAYERS):
        pawn = state.PawnPrivate or None
        if pawn is not None and pawn.GetLocalRole() != authority:
            return None
        found.append(Player(state, pawn, pawn is not None and on_foot(pawn),
                            pawn is not None and bool(pawn.IsLocallyControlled())))
    return sorted(found, key=lambda player: not player.host)


def player_name(state: Any, fallback: str) -> str:
    """The name the game shows for this player, read on his PlayerState, for the window and the screen only; fallback
    when it cannot be read. APlayerState.GetPlayerName is the engine's own reader (trials 9 and 10, seen in game)."""
    try:
        name = str(state.GetPlayerName()).strip()
    except Exception:
        return fallback
    return name[:MAX_NAME] if name else fallback
