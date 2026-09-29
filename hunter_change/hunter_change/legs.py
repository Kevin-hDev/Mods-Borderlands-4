"""The first-person legs of the played character. They hang from the body mesh at the feet and come with the hunter
worn, while the view stays at the played hunter's height: a taller hunter's legs then rise into the first-person view
(Amon's on Harlowe, essai 24). Scaled down in the ratio of the view heights, they stay under it, feet on the ground,
and the character keeps its size seen from outside (essai 26)."""

from itertools import islice
from typing import Any

import unrealsdk

from . import report

LEGS = "FirstPersonLegs"
MAX_CHILDREN = 40


def _legs_of(character: Any) -> Any:
    for child in islice(getattr(character.Mesh, "AttachChildren", None) or [], MAX_CHILDREN):
        if str(getattr(child, "Name", "")) == LEGS:
            return child
    return None


def fit(character: Any, scale: float) -> bool:
    """The legs scaled evenly by `scale`, 1 for whole; whether it was done."""
    legs = _legs_of(character)
    if legs is None:
        report.error_once("legs:missing", "the first-person legs were not found, left as they are")
        return False
    try:
        legs.SetRelativeScale3D(unrealsdk.make_struct("Vector", X=scale, Y=scale, Z=scale))
    except Exception as error:
        report.error_once("legs:refused", f"the first-person legs' scale was refused: {error!r}")
        return False
    return True
