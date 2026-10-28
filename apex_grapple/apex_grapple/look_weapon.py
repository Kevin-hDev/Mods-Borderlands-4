"""The weapon in the player's right hand, as the grapple gun's gestures stow it: a pistol or a long gun.

The game stows a pistol and the long guns in two ways each (its _Shared/AS_PS_* and AS_RH_* animations, read in its
archives on 2026-10-14). The weapon in hand is the character's first active slot (trial 2's arme_droite_essai.py);
its body names its kind last (Body_ORD_PS, Body_JAK_AR, read in game in trial 1). Heavy weapons have stows of their own,
not planned: they take the long guns' (conception-pistolet-et-gestes.md).
"""

from typing import Any

PISTOL, LONG = "PS", "RH"


def kind(character: Any) -> str | None:
    """PISTOL or LONG, or None with no weapon in hand."""
    weapon = character.ActiveWeapons.Slots[0].Weapon
    if weapon is None:
        return None
    body = str(getattr(weapon.BodyData, "Name", "") or "")
    return PISTOL if body.rsplit("_", 1)[-1] == PISTOL else LONG
