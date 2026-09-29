"""What the played character wears, and making it so: the loaded game's choice on each new character, a hunter chosen
now, and the own look back when the mod is turned off.

The look lives in the game's memory only and is lost when the game closes (essai 23): each new character of a game
with a choice is dressed again, and a game without one gets its own look back if its hunter's pickers are still
dressed from another game of the same session. Nothing is rebuilt when the look is already right: a game whose
player never chose is never touched. The legs belong to each character and are fitted on every new one (essai 29: a
fast travel or a death keeps the character, a load makes a new one, essai 30).
"""

from typing import Any

from mods_base import get_pc

from . import choices, hunters, legs, look, report
from .game_id import game_id
from .hunters import Hunter

DONE, WAIT, FAILED = "done", "wait", "failed"


def _worn(game: str, played: Hunter) -> Hunter:
    return hunters.by_code(choices.chosen(game) or "") or played


def _put_on(character: Any, player_state: Any, played: Hunter, worn: Hunter) -> bool:
    found = look.pickers(character)
    if found is None:
        return False
    if look.wearing(found) != worn and not look.dress(character, player_state, played, worn):
        return False
    legs.fit(character, hunters.legs_scale(played, worn))
    return True


def settle(character: Any, player_state: Any) -> str:
    """A new character dressed for its game: DONE, WAIT while the game is not ready, FAILED."""
    played = hunters.played(player_state)
    if played is None:
        return DONE
    game = game_id(player_state)
    found = look.pickers(character)
    if game is None or found is None:
        return WAIT
    worn = _worn(game, played)
    if worn == played and look.wearing(found) in (played, None):
        return DONE
    return DONE if _put_on(character, player_state, played, worn) else FAILED


def _in_play() -> tuple[Any, Any, Hunter, str] | None:
    pc = get_pc()
    character = getattr(pc, "OakCharacter", None) if pc is not None else None
    player_state = getattr(pc, "PlayerState", None) if pc is not None else None
    played = hunters.played(player_state)
    game = game_id(player_state)
    if character is None or played is None or game is None:
        return None
    return character, player_state, played, game


def status() -> tuple[Hunter, Hunter] | None:
    """The hunter played and the look it wears, for the window; None outside a game or while it is not ready."""
    now = _in_play()
    if now is None:
        return None
    character, _, played, _ = now
    found = look.pickers(character)
    if found is None:
        return None
    return played, look.wearing(found) or played


def wear(code: str) -> bool:
    """`code`'s look on the played character now, remembered for this game; the own hunter's forgets the choice."""
    now = _in_play()
    worn = hunters.by_code(code)
    if now is None or worn is None:
        report.error_once("wear:out", "no look changed: no game of one of the six hunters is loaded and ready")
        return False
    character, player_state, played, game = now
    if not _put_on(character, player_state, played, worn):
        return False
    choices.choose(game, None if worn == played else worn.code)
    return True


def undress() -> None:
    """The own look back on the played character and on every picker dressed this session; the choices are kept."""
    now = _in_play()
    if now is not None:
        character, player_state, played, _ = now
        found = look.pickers(character)
        if found is not None and look.wearing(found) != played:
            look.dress(character, player_state, played, played)
            legs.fit(character, 1.0)
    look.undress_all()
