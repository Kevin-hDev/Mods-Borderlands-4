"""Tells whether the camera has left the player's eyes: a third-person camera, one that looks from another actor, as in
a vehicle, or one still on its way back to them.

Why, 2026-09-25 (cosmetics/heirloom/docs/heirloom.md, the defect under its state): out of first person the game no
longer shows the first-person arms, but our knife, hung on them, stayed in view at the neck; Kevin wants no heirloom
there ("c'est pas fait pour ça"). The game hides the arms by none of their own fields: visible, not hidden, seen by
their owner, in third person as in first. What changes is the camera: its mode for the character, Default in first
person, Slide while sliding, ThirdPerson in third person; in a vehicle it looks from the vehicle (sondes/
apex_view_watch.py, verified in game).
Why, 2026-09-26 (cosmetics/heirloom/docs/enquetes/2026-09-26-arme-bloquee-apres-vehicule.md): getting out of a vehicle,
the camera already looks from the character, in Default, but flies back from 370 to 600 cm behind the eyes for 1.25 s,
and Kevin saw the knife float back into the hand; the game also gives the weapon back as it arrives
(sondes/apex_exit_camera_watch.py, verified in game). On foot it stays within 12 cm of the arms' Camera bone, which the
view follows (same log).
"""

import math
from typing import Any, Callable

Say = Callable[[str], None]
# Also inside the vehicle's own mode, ThirdPersonVehicle (Apex Movement's camera module, transitions.py).
THIRD_PERSON = "ThirdPerson"
EYE_BONE = "Camera"
# Well past the 12 cm seen on foot, well short of the 370 cm the camera starts back from.
AWAY_CM = 100.0
ON_ITS_WAY = "on its way back to the eyes"
# One line per kind of unreadable field, not one per frame: the watch runs at every frame.
REPORTED: set[str] = set()


def _unreadable(kind: str, error: Exception, say: Say) -> None:
    if kind not in REPORTED:
        REPORTED.add(kind)
        say(f"the camera's {kind} could not be read ({type(error).__name__}): the heirloom stays shown")


def third_person(reason: str) -> bool:
    return reason.startswith("in ")


def _far(manager: Any, arms_animation: Any) -> bool:
    eye, camera = arms_animation.Outer.GetSocketLocation(EYE_BONE), manager.GetCameraLocation()
    return math.dist((eye.X, eye.Y, eye.Z), (camera.X, camera.Y, camera.Z)) > AWAY_CM


def outside(manager: Any, character: Any, arms_animation: Any, say: Say) -> str:
    """Why the camera is out of the eyes of `character`, whose first-person arms play `arms_animation` ("in
    ThirdPerson", "from <actor>", ON_ITS_WAY), or "" while it looks through them. A camera that cannot be read counts as in the eyes: the
    knife then shows where Kevin would see it, and the reason is in the log."""
    if manager is None:
        return ""
    try:
        mode = str(manager.GetActorCameraMode(character))
        if THIRD_PERSON in mode:
            return f"in {mode}"
    except (AttributeError, TypeError, ValueError) as error:
        _unreadable("mode", error, say)
    try:
        target = manager.ViewTarget.Target
        if target is not None and target != character:
            return f"from {target.Name}"
    except (AttributeError, TypeError, ValueError) as error:
        _unreadable("view target", error, say)
    try:
        if _far(manager, arms_animation):
            return ON_ITS_WAY
    except (AttributeError, TypeError, ValueError) as error:
        _unreadable("place", error, say)
    return ""
