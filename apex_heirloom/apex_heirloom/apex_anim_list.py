"""Each heirloom's own lists of animations in the game, one per mode of the menu: the chosen heirloom's list of the
chosen mode given to empty hands through the game's picker, taken back, and whether the arms play that heirloom's
animations now.

Why, 2026-09-26 (cosmetics/heirloom/docs/enquetes/2026-09-25-listes-d-animations.md, essai 6, verified in game): our
container no longer replaces the game's unarmed animations; it holds ours in our own folder, with our own copy of the
game's list naming them (outils/pose/heirloom_lists.py). Added to the option the game's picker chooses for empty
hands, the list is read at the next weapon change, for empty hands only; taken out, the game's animations come back
at the next weapon change. The game reads its lists only then (essais 2 to 5), and Kevin chose that a setting applies
at the next weapon change (docs/mokup/menu_mods/decisions.md, 2026-09-26).

The picker is found by its full path, not through the arms: it is a game asset that outlives a character, and what
was added to it must be taken out even with no arms left. Why a list per mode, 2026-09-26: Kevin's Borderlands mode
keeps our rest, walk and sprint and gives the game's animations for the rest (heirloom.json, "lists"); only one of
our lists is ever given at a time. Why each heirloom's own, 2026-09-29 (docs/mokup/menu_mods/decisions.md): the knife's
and the axe's animations bear the same names; each heirloom's are in its own folders and container, all installed
together (heirloom_catalog.py, generated from their heirloom.json), and giving one heirloom's list takes back every
other one of ours.
"""

from itertools import islice
from typing import Any, Callable

import unrealsdk

from .heirloom_catalog import DEFAULT, HEIRLOOMS

Say = Callable[[str], None]
# Loads an asset by class and full path, or gives None (apex_held_object.load).
Load = Callable[[str, str], Any]

ANIMATIONS_ROOT = "/Game/PlayerCharacters/_Shared/Animation/1st/"
# The modes of the menu, the same for every heirloom offered (catalog_module.py refuses others); each heirloom's list
# folders sit beside the game's Unarmed and as long, and its animations live in its default mode's folder.
LISTS = {name: known["lists"] for name, known in HEIRLOOMS.items()}
MODES = tuple(LISTS[DEFAULT]["folders"])
DEFAULT_MODE = LISTS[DEFAULT]["default"]
LIST_CLASS = "GbxAnimSet"
PICKER_CLASS = "GbxAnimSetPicker"
# The package named in the game's files (donnees_jeu/extraction/ASetPicker_Player1st_Shared.json).
PICKER = "/Game/PlayerCharacters/_Shared/Animation/ASetPicker_Player1st_Shared.ASetPicker_Player1st_Shared"
UNARMED = "weapon_type_none"
# The picker's own field names, read in the game's files.
OPTIONS, OPTION_SETS = "options", "AnimSets"
# The role whose animation tells which list the arms read: every list has the rest.
ROLE = "AnimSet.Player.1st.Idle"
# Bounded above what was measured on 2026-09-25: 8 options, 2 lists in the option for empty hands.
MAX_ITEMS = 64

_failure_said = False


def folder(heirloom: str, mode: str) -> str:
    return f"{ANIMATIONS_ROOT}{LISTS[heirloom]['folders'][mode]}/"


def home(heirloom: str) -> str:
    """The folder of the heirloom's animations: its default mode's."""
    return folder(heirloom, LISTS[heirloom]["default"])


def animation(heirloom: str, name: str) -> str:
    """The full path of one of the heirloom's animations."""
    return f"{home(heirloom)}{name}.{name}"


def list_path(heirloom: str, mode: str) -> str:
    """The full path of the heirloom's list of a mode: each keeps the game's list's name, in its own folder."""
    return f"{folder(heirloom, mode)}ASet_Player1st_UA.ASet_Player1st_UA"


def every_list() -> set[str]:
    return {list_path(heirloom, mode) for heirloom, lists in LISTS.items() for mode in lists["folders"]}


def condition(option_struct: Any) -> str:
    """The name of the condition that makes the picker choose an option: a game definition, named by _name (as the
    stances, verified in game), or its text."""
    held = getattr(option_struct, "Condition", None)
    name = getattr(held, "_name", None)
    if name is not None:
        return str(name)
    name = getattr(held, "Name", None)
    return str(name) if name is not None else str(held)


def option(picker_object: Any, wanted: str) -> Any:
    """The picker's top-level option chosen by that condition (weapon_type_none...), or None."""
    for entry in islice(getattr(picker_object, OPTIONS), MAX_ITEMS):
        if condition(entry) == wanted:
            return entry
    return None


def unarmed_sets(say: Say) -> Any:
    """The lists the game's picker gives empty hands, or None, said, when the game has not loaded the picker."""
    try:
        picker = unrealsdk.find_object(PICKER_CLASS, PICKER)
    except ValueError:
        say("the game's picker of arm animations is not loaded: load into the game on foot first")
        return None
    unarmed = option(picker, UNARMED)
    if unarmed is None:
        say(f"the game's picker has no {UNARMED} option: the game changed")
        return None
    return getattr(unarmed, OPTION_SETS)


def _take_back(sets: Any, keep: str | None) -> int:
    """Takes our lists, every heirloom's, but `keep` out of `sets`; how many were taken."""
    ours = every_list() - {keep}
    taken = 0
    for index in reversed(range(min(len(sets), MAX_ITEMS))):
        if str(sets[index]._path_name()) in ours:
            del sets[index]
            taken += 1
    return taken


def add(load: Load, heirloom: str, mode: str, say: Say) -> bool:
    """Gives the heirloom's list of the mode to empty hands, once, in place of any other of ours; False, said, when it
    cannot."""
    if heirloom not in LISTS:
        say(f"no {heirloom!r} heirloom: the heirlooms are {', '.join(LISTS)}")
        return False
    if mode not in LISTS[heirloom]["folders"]:
        say(f"no {mode!r} mode: the modes are {', '.join(LISTS[heirloom]['folders'])}")
        return False
    sets = unarmed_sets(say)
    if sets is None:
        return False
    wanted = list_path(heirloom, mode)
    ours = load(LIST_CLASS, wanted)
    if ours is None:
        say(f"our {heirloom} animations are not in the game: is {LISTS[heirloom]['container']} installed?")
        return False
    _take_back(sets, wanted)
    if any(entry == ours for entry in islice(sets, MAX_ITEMS)):
        say(f"our {heirloom} {mode} animations were already given to empty hands")
        return True
    sets.append(ours)
    say(f"our {heirloom} {mode} animations given to empty hands: they play from the next weapon change")
    return True


def remove(say: Say) -> int:
    """Takes every one of our lists back from empty hands; how many entries were taken."""
    sets = unarmed_sets(say)
    if sets is None:
        return 0
    taken = _take_back(sets, None)
    say(f"our animations taken back from empty hands ({taken}): the game's play from the next weapon change")
    return taken


def played(arms_animation: Any, heirloom: str, say: Say) -> bool:
    """Whether the arms play the heirloom's animations now: not while another heirloom's still play, until the next
    weapon change. A failure to tell counts as not: the heirloom then hides rather than shows over the game's hands;
    it is said once."""
    global _failure_said
    try:
        found = arms_animation.GetAnimationFromTag(unrealsdk.make_struct("GameplayTag", TagName=ROLE))
        return found is not None and str(found._path_name()).startswith(home(heirloom))
    except Exception as error:
        if not _failure_said:
            _failure_said = True
            say(f"which animations the arms play could not be read: {error!r}")
        return False
