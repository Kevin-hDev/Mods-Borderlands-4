"""Which climb loop the third-person body plays, by the hunter being played.

The hunter is read in the character's own definition, GbxActorData.GbxActorDef, written FGbxDefPtr('Char_<class>', ...)
in the log. Only its first name counts: Loveless's definition names Char_DarkSiren further in (read in game on
2026-10-14). Not by the body's skeleton: every hunter has three bodies, each with its own skeleton (the base one, Prison
and Premium; C4SH flew wearing Premium on 2026-10-25), and the game declares all of them compatible with one another.

Loops as read in the game's files on 2026-10-25. Only Vex and C4SH have the game's wall-climb set, a mechanic it left
unused; every hunter has its own ladder ascent, the loop the body's animation graph names for the game's climbing walls
(AnimSet.Player.3rd.Ladder_Ascend). The first one in memory is played: Vex's wall climb was there on 2026-09-23. On
2026-10-25 the ladder ascents of Amon, Rafa, Harlowe and Loveless played on their base bodies, and C4SH's wall climb on
his Premium body. Vex's and C4SH's ladder ascents, their second choice, have never been needed.
"""

import re
from typing import Any

import unrealsdk

from . import report

FIRST_NAME = re.compile(r"FGbxDefPtr\('?Char_(\w+)")
_SKILLS = "/Game/{root}PlayerCharacters/{hunter}/Animation/3rd/CharacterSkills/{name}.{name}"
_WALL = "AS_Wall_Climb_U"
_LADDER = "AS_Ladder_Ascend"


def _loops(hunter: str, root: str, names: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_SKILLS.format(root=root, hunter=hunter, name=name) for name in names)


LOOPS = {
    "DarkSiren": _loops("DarkSiren", "", (_WALL, _LADDER)),
    "RoboDealer": _loops("RoboDealer", "DLC/Cowbell/", (_WALL, _LADDER)),
    "Paladin": _loops("Paladin", "", (_LADDER,)),
    "ExoSoldier": _loops("ExoSoldier", "", (_LADDER,)),
    "Gravitar": _loops("Gravitar", "", (_LADDER,)),
    "CorpoHacker": _loops("CorpoHacker", "DLC/Harmonica/", (_LADDER,)),
}


def hunter(character: Any) -> str:
    """The class the definition names first, or 'unknown'. Raises when the definition cannot be read."""
    found = FIRST_NAME.match(str(character.GbxActorData.GbxActorDef))
    return found.group(1) if found else "unknown"


def loop_for(character: Any) -> Any:
    """The hunter's first climb loop in memory, or None; each miss is said once, naming the hunter and what it lacks."""
    try:
        name = hunter(character)
    except Exception as error:
        report.error_once("climb_loops:hunter", f"body climb animation unavailable: hunter unreadable ({error!r})")
        return None
    paths = LOOPS.get(name)
    if paths is None:
        report.error_once(f"climb_loops:unknown:{name}", f"body climb animation unavailable: no climb known for {name}")
        return None
    for path in paths:
        try:
            return unrealsdk.find_object("AnimSequence", path)
        except ValueError:
            continue
    report.error_once(f"climb_loops:absent:{name}",
                      f"body climb animation unavailable for {name}: none in memory of {', '.join(paths)}")
    return None
