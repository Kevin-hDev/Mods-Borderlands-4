"""The player in the running game: his controller, his body on foot, his level.

The level's recipe is the save editor's, verified in game (docs/candidats/editeur_de_sauvegarde, probes 1 and
23): the experience tracks are PlayerState.ExperienceState, and the character's own is the one whose ExperienceId
prints `Name: 'Character'`.
"""

import re
from itertools import islice
from typing import Any

from mods_base import get_pc

from . import report

CHARACTER_TRACK = "Character"
# Bounded: the game held 7 tracks when the save editor measured it.
MAX_TRACKS = 12
TRACK_NAME = re.compile(r"""Name:\s*['"]([^'"]+)['"]""")


def current() -> tuple[Any, Any]:
    """(controller, character on foot); the character is None in a menu, a loading or a vehicle."""
    pc = get_pc(possibly_loading=True)
    return pc, (getattr(pc, "OakCharacter", None) if pc is not None else None)


def level(pc: Any) -> int:
    """The character's level; 1, said once, when the game will not give it."""
    try:
        for track in islice(pc.PlayerState.ExperienceState, MAX_TRACKS):
            match = TRACK_NAME.search(str(track.ExperienceId))
            if match and match.group(1) == CHARACTER_TRACK:
                return max(1, int(track.ExperienceLevel))
    except Exception as error:
        report.error_once("level", f"the level could not be read, the beam hits as at level 1: {type(error).__name__}")
        return 1
    report.error_once("level", "no experience track named Character, the beam hits as at level 1")
    return 1
