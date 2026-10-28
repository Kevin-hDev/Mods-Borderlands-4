"""What the played character wears, and making it so: the loaded game's choice on each new character, a hunter or a
skin of its body or head chosen now, and the own look back when the mod is turned off.

The look lives in the game's memory only and is lost when the game closes (essai 23): each new character of a game
with a choice is dressed again, and a game without one gets its own look back if its hunter's pickers are still
dressed from another game of the same session. Nothing is rebuilt when the look is already right: a game whose
player never chose is never touched. The size belongs to each character and is given on every new one (stature.py;
essai 29: a fast travel or a death keeps the character, a load makes a new one, essai 30).

A skin is offered only to its owner (skins.py) and remembered only then; a game's choice is worn again as remembered,
without asking the game again: right after a load, the game may not have told yet what the player owns.
"""

from typing import Any, NamedTuple

from mods_base import get_pc

from . import choices, hunters, look, report, skins, stature
from .game_id import game_id
from .hunters import BODY, DEFAULT, HEAD, Hunter

DONE, WAIT, FAILED = "done", "wait", "failed"
PARTS = (BODY, HEAD)


class Look(NamedTuple):
    """The hunter worn and the skins of its body and head; the own hunter's is always with the game's own skins. A
    skin read from the game may be None: a part of none of the skins."""
    hunter: Hunter
    body: str | None = DEFAULT
    head: str | None = DEFAULT


class Status(NamedTuple):
    """What the window shows: the hunter played, the look worn, and the skins the player owns."""
    played: Hunter
    worn: Look
    owned: tuple[str, ...]


def _worn(game: str, played: Hunter) -> Look:
    choice = choices.chosen(game)
    hunter = hunters.by_code(choice.hunter) if choice is not None else None
    if hunter is None or hunter == played:
        return Look(played)
    return Look(hunter, choice.body, choice.head)


def _wearing(found: dict[str, Any]) -> Look | None:
    hunter = look.wearing(found)
    return Look(hunter, *look.skins_worn(found)) if hunter is not None else None


def _put_on(character: Any, player_state: Any, played: Hunter, worn: Look) -> bool:
    found = look.pickers(character)
    if found is None:
        return False
    if _wearing(found) != worn and not look.dress(character, player_state, played, *worn):
        return False
    stature.wear(character, worn.hunter)
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
    if worn == Look(played) and look.wearing(found) in (played, None):
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


def _shown(found: dict[str, Any], played: Hunter) -> Look:
    """The look the window shows, read on the character: a body the mod does not know shown as the own look, which
    the mod leaves alone; a head it does not know, as no skin."""
    worn = _wearing(found)
    return Look(played) if worn is None or worn.hunter == played else worn


def status() -> Status | None:
    """What the window shows; None outside a game or while it is not ready."""
    now = _in_play()
    if now is None:
        return None
    character, _, played, _ = now
    found = look.pickers(character)
    if found is None:
        return None
    return Status(played, _shown(found, played), skins.owned())


def _change(make: Any) -> bool:
    """The look `make(played, current, owned)` gives, on the played character now and remembered for this game; the
    own hunter's forgets the choice. False when no game is ready or the look is refused.

    `current` is the look the window shows, read on the character, not the game's choice: the two differ when the
    choice could not be worn on a new character, and a click must act on what the player sees (audit, 2026-10-07)."""
    now = _in_play()
    found = look.pickers(now[0]) if now is not None else None
    if now is None or found is None:
        report.error_once("wear:out", "no look changed: no game of one of the six hunters is loaded and ready")
        return False
    character, player_state, played, game = now
    shown = _shown(found, played)
    current = shown._replace(**{name: skin or DEFAULT for name, skin in (("body", shown.body), ("head", shown.head))})
    worn = make(played, current, skins.owned())
    if worn is None or not _put_on(character, player_state, played, worn):
        return False
    if worn.hunter == played:
        choices.choose(game, None)
    else:
        choices.choose(game, worn.hunter.code, worn.body, worn.head)
    return True


def wear(code: str) -> bool:
    """`code`'s look now, keeping the body and head chosen when the player owns them; the own hunter's look forgets
    the choice."""
    hunter = hunters.by_code(code)
    if hunter is None:
        report.error_once("wear:unknown", "no look changed: the hunter chosen is none of the six")
        return False

    def make(played: Hunter, current: Look, owned: tuple[str, ...]) -> Look:
        if hunter == played:
            return Look(played)
        return Look(hunter, *(skin if skin in owned else DEFAULT for skin in current[1:]))

    return _change(make)


def wear_skin(part: str, skin: str) -> bool:
    """The body or head of the look worn in `skin` now, if the player owns it; refused on the own look, whose skins
    are the game's."""

    def make(played: Hunter, current: Look, owned: tuple[str, ...]) -> Look | None:
        if part not in PARTS or skin not in owned or current.hunter == played:
            report.error_once(f"skin:{part}:{skin}", f"no skin changed: {skin} for the {part.strip('_').lower()} "
                                                     "is not offered on this look")
            return None
        return current._replace(**{"body" if part == BODY else "head": skin})

    return _change(make)


def undress() -> None:
    """The own look and size back on the played character, the own look on every picker dressed this session; the
    choices are kept."""
    now = _in_play()
    if now is not None:
        character, player_state, played, _ = now
        found = look.pickers(character)
        if found is not None and _wearing(found) != Look(played):
            look.dress(character, player_state, played, played)
            stature.wear(character, played)
    stature.forget()
    look.undress_all()
