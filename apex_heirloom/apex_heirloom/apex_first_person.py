"""The first-person arms: the mesh the player sees of his own hands, and what can be hung on it.

Shared by every probe that draws or attaches anything to the hand. Two copies of this lookup would
drift apart.

Recipe verified in Apex Movement (session F, 2026-09-17) and used by Apex Grapple since: the arms
are the animation instance whose mesh is named FirstPersonArms, belongs to the character, and
answers with that same instance.
"""

from itertools import islice
from typing import Any

import unrealsdk

ANIM_INSTANCE = "/Script/Engine.AnimInstance"
ARMS_MESH = "FirstPersonArms"
# Bounded: a level held 202 to 322 animation instances when Apex Movement measured it.
MAX_ANIM_INSTANCES = 20_000
# Every bone of the arms is an anchor too: Kevin's arms mesh has 325 bones (extraction of 2026-09-23). A bound of
# 120 cut the list that day and hid R_Hand_Object, so a probe hung its object in the other hand.
MAX_SOCKETS = 2_000


def mesh(owner: Any) -> Any:
    """The mesh of the first-person arms, or None while the game has not built it."""
    if owner is None:
        return None
    for instance in islice(unrealsdk.find_all(ANIM_INSTANCE, exact=False), MAX_ANIM_INSTANCES):
        found = instance.Outer
        if (found is not None and str(found.Name) == ARMS_MESH and found.Outer == owner
                and found.GetAnimInstance() == instance):
            return found
    return None


def sockets(arms: Any) -> list[str]:
    """Every anchor the arms carry, so a hand is never guessed at. Empty when the game will not say."""
    reader = getattr(arms, "GetAllSocketNames", None)
    if reader is None:
        return []
    try:
        return [str(name) for name in islice(reader(), MAX_SOCKETS)]
    except Exception:
        return []
