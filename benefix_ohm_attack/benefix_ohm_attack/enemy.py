"""What the mod reads of a character of the game: where it stands, whether it is dead, whether it is a friend.

Where and dead are the enemy probes' readings, verified in game in September 2026 (mods/perso/apex_probe):
K2_GetActorLocation, and HealthState.bCurrentlyDead. Friend is asked of the game's own team library,
GbxTeamFunctionLibrary.GetAttitudeTowards, whose answer is the engine's ETeamAttitude (friendly, neutral,
hostile: read in the game's field map on 2026-10-02). That call was never made before this mod: its first asking
of a session is written in the log before it is made, its answer after, and a game that refuses it is not asked
again. Nobody is a friend then, as before the beam could lock (aim.py tells allies by their name only).
"""

import math
from typing import Any

import unrealsdk

from . import aim, report

TEAMS, ATTITUDE = "GbxTeamFunctionLibrary", "GetAttitudeTowards"
FRIENDLY_NAME, FRIENDLY_NUMBER = "friendly", 0
MAX_COORDINATE = 1e9
# How much of the game's answer the log shows.
MAX_SHOWN = 60

_attitude_refused = False
_attitude_said = False


def forget() -> None:
    global _attitude_refused, _attitude_said
    _attitude_refused = False
    _attitude_said = False


def place(actor: Any) -> tuple[float, float, float] | None:
    """Where the character stands; None when it cannot say, as one that has just left the world."""
    try:
        spot = actor.K2_GetActorLocation()
        found = (float(spot.X), float(spot.Y), float(spot.Z))
    except Exception:
        return None
    return found if all(math.isfinite(value) and abs(value) <= MAX_COORDINATE for value in found) else None


def dead(actor: Any) -> bool:
    """Whether the game counts the character dead; alive, said once, when that cannot be read."""
    try:
        return bool(actor.HealthState.bCurrentlyDead)
    except Exception as error:
        report.error_once("enemy:dead", f"a character's death could not be read, it counts as alive: {error!r}")
        return False


def _is_friendly(answer: Any) -> bool:
    name = getattr(answer, "name", None)
    if name is not None:
        return str(name).lower() == FRIENDLY_NAME
    return type(answer) is int and answer == FRIENDLY_NUMBER


def friend(character: Any, actor: Any) -> bool:
    """Whether the game says the player is friendly towards that character: his own summons, his allies."""
    global _attitude_refused, _attitude_said
    if _attitude_refused:
        return False
    first = not _attitude_said
    if first:
        _attitude_said = True
        report.note(f"first attitude asked, towards {aim.species_of(actor)}")
    try:
        answer = getattr(unrealsdk.find_class(TEAMS).ClassDefaultObject, ATTITUDE)(character, actor)
    except Exception as error:
        _attitude_refused = True
        report.error_once("enemy:friend", f"the game will not say who is a friend, the beam locks on any "
                                          f"character: {error!r}")
        return False
    if first:
        report.note(f"the game answered {repr(answer)[:MAX_SHOWN]}")
    return _is_friendly(answer)
