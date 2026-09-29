"""The six playable hunters: the one place that names them, tells which one a player state plays, measures them, names
their default parts and the group of their skill tree."""

from dataclasses import dataclass
from typing import Any

# The endings of the two pickers whose default parts make a hunter's whole look: body and head.
BODY, HEAD = "_Body", "_Head"


@dataclass(frozen=True)
class Hunter:
    code: str
    name: str
    # Capsule half height plus eye height, in game units, measured in each hunter's own game (essai 27, 2026-09-28).
    view_height: float
    # The group_def_name of the hunter's skill tree in a save, read in Kevin's saves on 2026-09-28. Loveless's, whose
    # tree never loaded in Kevin's game, read in the game's progress_graph_group table (pakchunk0-Windows_20_P.pak),
    # where the five others are spelled as the saves write them.
    tree_group: str


# In the menu's order (sketch B2, chosen by Kevin on 2026-09-28).
HUNTERS = (
    Hunter("DarkSiren", "Vex", 164.0, "ProgressGroup_DarkSiren"),
    Hunter("ExoSoldier", "Rafa", 177.0, "progress_group_exo"),
    Hunter("Gravitar", "Harlowe", 153.0, "progress_group_gravitar"),
    Hunter("Paladin", "Amon", 217.0, "ProgressGroup_Paladin"),
    Hunter("RoboDealer", "C4SH", 195.0, "ProgressGroup_Robodealer"),
    Hunter("CorpoHacker", "Loveless", 181.5, "ProgressGroup_Corpohacker"),
)
_BY_CODE = {hunter.code: hunter for hunter in HUNTERS}
CHARACTER_PREFIX = "Char_"


def by_code(code: str) -> Hunter | None:
    return _BY_CODE.get(code)


def by_character(definition: str) -> Hunter | None:
    """The hunter of a character definition as the game names it, Char_<code>."""
    return by_code(definition.removeprefix(CHARACTER_PREFIX)) if definition.startswith(CHARACTER_PREFIX) else None


def played(player_state: Any) -> Hunter | None:
    """The hunter a player state plays, from its character definition; None without a player state, as during a load,
    or without one of the six."""
    return by_character(str(getattr(player_state, "ReplicatedCharacterDef", "")))


def parts(hunter: Hunter) -> dict[str, str]:
    """The default body and head, named alike for every hunter in the game's files (NCS GbxActorPart)."""
    return {BODY: f"Cosmetics_{hunter.code}_Body00_Default", HEAD: f"Cosmetics_{hunter.code}_Head00_Default"}


def legs_scale(played: Hunter, worn: Hunter) -> float:
    """The first-person legs of a taller hunter worn stand above the played one's view unless scaled down in the
    ratio of their view heights (essai 26: Amon's on Harlowe); a smaller hunter's are kept whole."""
    return min(1.0, played.view_height / worn.view_height)
