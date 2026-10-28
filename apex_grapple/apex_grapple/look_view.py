"""Which view the player sees the grapple gun from: through the eyes or from behind, read on the camera at each call.

The camera's mode holds ThirdPerson in the game's own third person (Benefix Ohm Attack's view.py, verified in game on
2026-10-01), but not always in Kevin's, Apex Movement's camera: during trial 1 (2026-10-04) the mode lost it while
Kevin kept watching Vex from behind, and the camera stayed over a metre from her eyes. So a camera this far from the
character along the ground is third person too: through the eyes it stays within 12 cm of them on foot (Apex
Heirloom's apex_camera_view.py, verified in game). docs/apex_grapple/pistolet-grappin/sondes/essai_commun.py read it
this way through every trial since.
"""

import math
from typing import Any

FIRST, THIRD = "first", "third"
THIRD_PERSON = "ThirdPerson"
AWAY_CM = 100.0


def of(pc: Any, character: Any, here: tuple[float, float, float] | None = None) -> str:
    """`here` is the character's place when the caller has just read it in this frame."""
    manager = pc.PlayerCameraManager
    if THIRD_PERSON in str(manager.GetActorCameraMode(character)):
        return THIRD
    eye = manager.GetCameraLocation()
    if here is None:
        spot = character.K2_GetActorLocation()
        here = (float(spot.X), float(spot.Y), float(spot.Z))
    gap = math.hypot(float(eye.X) - here[0], float(eye.Y) - here[1])
    return THIRD if gap >= AWAY_CM else FIRST
