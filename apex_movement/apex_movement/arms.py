"""Finds the first-person arms' animation: what the player sees of a climb.

character.FirstPersonArms is no Python attribute (session E, 2026-09-17): the arms are the animation instance whose
mesh is named FirstPersonArms, belongs to the character and answers with that instance (session F). Looked up once,
when first needed; game.py drops it whenever the player or the player's animation changes.

Split from game.py on 2026-09-18: it had reached 230 lines holding the player, the assets, the arms and the state
every movement reads.
"""

from itertools import islice
from typing import Any

import unrealsdk

ANIM_INSTANCE = "/Script/Engine.AnimInstance"
ARMS_MESH = "FirstPersonArms"
# Bounded: a level held 202 to 322 animation instances in sessions F and G (2026-09-17).
MAX_ANIM_INSTANCES = 20_000

_arms: Any = None


def find(character: Any) -> Any:
    """The character's first-person arms' animation; None while it is not found, looked up again at the next call."""
    global _arms
    if _arms is None and character is not None:
        for instance in islice(unrealsdk.find_all(ANIM_INSTANCE, exact=False), MAX_ANIM_INSTANCES):
            mesh = instance.Outer
            if (mesh is not None and str(mesh.Name) == ARMS_MESH and mesh.Outer == character
                    and mesh.GetAnimInstance() == instance):
                _arms = instance
                break
    return _arms


def forget() -> None:
    global _arms
    _arms = None
