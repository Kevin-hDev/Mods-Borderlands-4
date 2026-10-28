"""The six playable hunters: the one place that names them, tells which one a player state plays, measures them, names
the body and head parts of their skins and the group of their skill tree."""

from dataclasses import dataclass
from typing import Any

# The endings of the two pickers whose default parts make a hunter's whole look: body and head.
BODY, HEAD = "_Body", "_Head"


# Common to the six, measured in each one's own game (2026-10-08): the capsule's radius and its half height crouched.
RADIUS, CROUCHED_HALF = 40.0, 60.5


@dataclass(frozen=True)
class Stature:
    """A hunter's own size, in game units, measured in each one's own game (2026-10-08, enquête
    2026-10-07-taille-du-chasseur-porte): the capsule's half height, the eye heights standing and crouched, and how
    far under the capsule's centre the body hangs (one more than the half height for Harlowe alone)."""
    half: float
    eye: float
    crouched_eye: float
    mesh_z: float


@dataclass(frozen=True)
class Hunter:
    code: str
    name: str
    stature: Stature
    # The group_def_name of the hunter's skill tree in a save, read in Kevin's saves on 2026-09-28. Loveless's, whose
    # tree never loaded in Kevin's game, read in the game's progress_graph_group table (pakchunk0-Windows_20_P.pak),
    # where the five others are spelled as the saves write them.
    tree_group: str


# In the menu's order (sketch B2, chosen by Kevin on 2026-09-28).
HUNTERS = (
    Hunter("DarkSiren", "Vex", Stature(93.0, 71.0, 39.5, -93.0), "ProgressGroup_DarkSiren"),
    Hunter("ExoSoldier", "Rafa", Stature(100.0, 77.0, 54.5, -100.0), "progress_group_exo"),
    Hunter("Gravitar", "Harlowe", Stature(86.0, 67.0, 48.5, -87.0), "progress_group_gravitar"),
    Hunter("Paladin", "Amon", Stature(115.0, 102.0, 69.5, -115.0), "ProgressGroup_Paladin"),
    Hunter("RoboDealer", "C4SH", Stature(105.0, 90.0, 62.5, -105.0), "ProgressGroup_Robodealer"),
    Hunter("CorpoHacker", "Loveless", Stature(100.0, 81.5, 59.0, -100.0), "ProgressGroup_Corpohacker"),
)
_BY_CODE = {hunter.code: hunter for hunter in HUNTERS}
CHARACTER_PREFIX = "Char_"

# The three skins of every hunter's body and head, in the window's order (sketch C1, Kevin, 2026-10-07): the game's
# own, the prison prologue's, and the Ornate Order Pack's, whose head is the 16th (read in the game's files,
# 2026-10-07).
DEFAULT, PRISON, PREMIUM = "default", "prison", "premium"
SKINS = (DEFAULT, PRISON, PREMIUM)
_ENDINGS = {BODY: {DEFAULT: "Body00_Default", PRISON: "Body01_Prison", PREMIUM: "Body02_Premium"},
            HEAD: {DEFAULT: "Head00_Default", PRISON: "Head01_Prison", PREMIUM: "Head16_Premium"}}
_BY_PART = {f"Cosmetics_{hunter.code}_{ending}": (hunter, skin)
            for hunter in HUNTERS for endings in _ENDINGS.values() for skin, ending in endings.items()}


def by_code(code: str) -> Hunter | None:
    return _BY_CODE.get(code)


def by_character(definition: str) -> Hunter | None:
    """The hunter of a character definition as the game names it, Char_<code>."""
    return by_code(definition.removeprefix(CHARACTER_PREFIX)) if definition.startswith(CHARACTER_PREFIX) else None


def played(player_state: Any) -> Hunter | None:
    """The hunter a player state plays, from its character definition; None without a player state, as during a load,
    or without one of the six."""
    return by_character(str(getattr(player_state, "ReplicatedCharacterDef", "")))


def parts(hunter: Hunter, body: str = DEFAULT, head: str = DEFAULT) -> dict[str, str]:
    """The body and head of the skins named, named alike for every hunter in the game's files (NCS GbxActorPart)."""
    return {BODY: f"Cosmetics_{hunter.code}_{_ENDINGS[BODY][body]}",
            HEAD: f"Cosmetics_{hunter.code}_{_ENDINGS[HEAD][head]}"}


def part_of(name: str) -> tuple[Hunter, str] | None:
    """The hunter and skin of a body or head part, by its name; None for a part that is none of theirs."""
    return _BY_PART.get(name)
