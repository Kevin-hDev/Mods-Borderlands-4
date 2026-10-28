"""The played character's look: its body and head pickers, the outfit it wears, and dressing it as a hunter.

Verified in game (docs/reverse-and-change-hunters): a hunter's whole look comes from the default parts of its body
and head pickers, which the game builds from while those two selections are Default (essais 22 to 24). A default part
is written as a reference made by name and typed as the picker's own default: the field is typed, so the SDK checks it
(a typed reference given to an untyped GbxDefPtr parameter crashes the game, 2026-09-28). The game builds again when
handed a text that changes the selections: first one of the body picker's own parts, then the outfit worn, whose text
is the save's own (essai 30). To show another hunter, the outfit goes back without its body and head, which the game
then keeps Default, and saves so (essai 31); the rest of the outfit, colours included, stays. Any of the three skins'
body and head can be written so (a player's report, Nexus, 2026-10-07), if the player owns it (skins.py). The outfit
is the game's business: the mod never keeps nor restores one (Kevin, 2026-09-28), it hands back what is worn.

The pickers live the whole game session and are shared by every game of a hunter (essai 23): the ones dressed are
listed, so that turning the mod off gives every one its own default back.
"""

from itertools import islice
from typing import Any

from unrealsdk.unreal import FGbxDefPtr

from . import hunters, report
from .hunters import BODY, DEFAULT, HEAD, Hunter

ACTOR_TYPE = "character"
CHOSEN = "def"
MAX_SELECTIONS = 12
MAX_CHOICES = 8
# Two pickers for each of the six hunters.
MAX_DRESSED = 12

_dressed: dict[str, tuple[Any, Hunter]] = {}


def name_of(definition: Any) -> str:
    try:
        return str(definition._name)
    except AttributeError:
        return ""


def pickers(character: Any) -> dict[str, Any] | None:
    """The body and head pickers among the character's selections; None without both."""
    found: dict[str, Any] = {}
    try:
        selections = character.GbxActorPartOwnerState.ReplicatedSelections
    except AttributeError:
        return None
    for selection in islice(selections, MAX_SELECTIONS):
        for ending in (BODY, HEAD):
            if name_of(selection.SelectorDef).endswith(ending):
                found[ending] = selection.SelectorDef
    return found if set(found) == {BODY, HEAD} else None


def wearing(found: dict[str, Any]) -> Hunter | None:
    """The hunter whose body, of any skin, the body picker holds as its default."""
    worn = hunters.part_of(name_of(found[BODY].DefaultPart))
    return worn[0] if worn is not None else None


def skins_worn(found: dict[str, Any]) -> tuple[str | None, str | None]:
    """The skins of the body and head the pickers hold as their defaults; None for a part of none of the skins."""
    worn = [hunters.part_of(name_of(found[ending].DefaultPart)) for ending in (BODY, HEAD)]
    return tuple(part[1] if part is not None else None for part in worn)


def kind_of(choice: Any) -> str:
    """A choice's kind by its name: the SDK hands an int enum, whose str() is its number (essai 29)."""
    kind = getattr(choice, "type", None)
    return str(getattr(kind, "name", kind))


def outfit(character: Any) -> list[tuple[str, str]]:
    """Picker and part of each chosen part, in the game's order."""
    entries: list[tuple[str, str]] = []
    for selection in islice(character.GbxActorPartOwnerState.ReplicatedSelections, MAX_SELECTIONS):
        for choice in islice(selection.choices, MAX_CHOICES):
            if kind_of(choice) == CHOSEN:
                entries.append((name_of(selection.SelectorDef), name_of(choice.ChosenDef)))
    return entries


def outfit_text(entries: list[tuple[str, str]]) -> str:
    return "gap," + ",".join(f"{picker}[{part}]" for picker, part in entries)


def _write(found: dict[str, Any], hunter: Hunter, body: str = DEFAULT, head: str = DEFAULT) -> bool:
    for ending, name in hunters.parts(hunter, body, head).items():
        picker = found[ending]
        try:
            picker.DefaultPart = FGbxDefPtr(name, picker.DefaultPart._type)
        except Exception as error:
            report.error_once(f"write:{hunter.code}", f"{hunter.name}'s parts were refused: {error!r}")
            return False
        if name_of(picker.DefaultPart) != name:
            report.error_once(f"write:{hunter.code}", f"{hunter.name}'s parts did not take")
            return False
    return True


def _track(found: dict[str, Any], played: Hunter, worn: Hunter) -> None:
    for picker in found.values():
        name = name_of(picker)
        if worn == played:
            _dressed.pop(name, None)
        elif name in _dressed or len(_dressed) < MAX_DRESSED:
            _dressed[name] = (picker, played)


def _rebuild(player_state: Any, body_picker: Any, text: str) -> bool:
    # The first text makes the second a change even when it equals the outfit worn, so the game always builds again.
    first = f"gap,{name_of(body_picker)}[{name_of(body_picker.PickableParts[0])}]"
    for handed in (first, text):
        try:
            player_state.ServerSetGbxActorParts(ACTOR_TYPE, handed)
        except Exception as error:
            report.error_once("rebuild", f"the game refused to rebuild the character: {error!r}")
            return False
    return True


def dress(character: Any, player_state: Any, played: Hunter, worn: Hunter, body: str = DEFAULT,
          head: str = DEFAULT) -> bool:
    """The character built as `worn` with the body and head of the skins named, its own look when `worn` is
    `played`, keeping the rest of the outfit worn. The own look always takes the game's own parts: the player's own
    skins are chosen in the outfit, which is handed back whole."""
    found = pickers(character)
    if found is None or not found[BODY].PickableParts:
        report.error_once("pickers", "the character's body and head pickers were not found, look unchanged")
        return False
    if worn == played:
        body = head = DEFAULT
    if not _write(found, worn, body, head):
        _write(found, played)
        _track(found, played, played)
        return False
    _track(found, played, worn)
    entries = outfit(character)
    if worn != played:
        body_and_head = {name_of(found[BODY]), name_of(found[HEAD])}
        entries = [entry for entry in entries if entry[0] not in body_and_head]
    if not _rebuild(player_state, found[BODY], outfit_text(entries)):
        # The character still draws its old look: the pickers go back to match it, or a reload would show `worn`.
        _write(found, played)
        _track(found, played, played)
        return False
    report.note(f"{played.name} wears {worn.name}'s look, body {body}, head {head}")
    return True


def undress_all() -> None:
    """Every picker dressed this session given its own default back; a character already drawn keeps its look until
    the game builds it again."""
    for name, (picker, own) in list(_dressed.items()):
        own_part = hunters.parts(own)[BODY if name.endswith(BODY) else HEAD]
        try:
            picker.DefaultPart = FGbxDefPtr(own_part, picker.DefaultPart._type)
        except Exception as error:
            report.error_once(f"undress:{name}", f"{own.name}'s own parts were refused: {error!r}")
            continue
        del _dressed[name]
