"""Finds the first-person arms' animation: what the player sees of his own hands.

Recipe verified in Apex Movement (session F, 2026-09-17): character.FirstPersonArms is no Python
attribute. The arms are the animation instance whose mesh is named FirstPersonArms, belongs to the
character, and answers with that same instance.

Its own copy rather than Apex Movement's: two mods sharing a package name would fight over the same
import and only one would load.
"""

from itertools import islice
from typing import Any

import unrealsdk
from unrealsdk import unreal

ANIM_INSTANCE = "/Script/Engine.AnimInstance"
ARMS_MESH = "FirstPersonArms"
# Bounded: a level held 202 to 322 animation instances when Apex Movement measured it.
MAX_ANIM_INSTANCES = 20_000

_arms: Any = None


def find(character: Any) -> Any:
    """The character's first-person arms' animation; None while not found, looked up again next call."""
    global _arms
    cached = _arms() if _arms is not None else None
    if cached is not None:
        mesh = cached.Outer
        if mesh is None or mesh.Outer != character or mesh.GetAnimInstance() != cached:
            cached = None
    if cached is None and character is not None:
        for instance in islice(unrealsdk.find_all(ANIM_INSTANCE, exact=False), MAX_ANIM_INSTANCES):
            mesh = instance.Outer
            if (mesh is not None and str(mesh.Name) == ARMS_MESH and mesh.Outer == character
                    and mesh.GetAnimInstance() == instance):
                cached = instance
                break
    _arms = unreal.WeakPointer(cached) if cached is not None else None
    return cached


def forget() -> None:
    global _arms
    _arms = None
