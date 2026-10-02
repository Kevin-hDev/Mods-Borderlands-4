"""Which view the player has: through the character's eyes, or from behind in third person.

The camera's mode for the character says it: Default in first person, a name holding ThirdPerson in third person
(the heirloom's apex_camera_view.py, verified in game on 2026-09-25). A camera that cannot be read counts as first
person, said once: the beam then leaves from the first-person arms, as it always did.
"""

from typing import Any

from . import report

THIRD_PERSON = "ThirdPerson"


def third_person(pc: Any, character: Any) -> bool:
    try:
        return THIRD_PERSON in str(pc.PlayerCameraManager.GetActorCameraMode(character))
    except Exception as error:
        report.error_once("view", f"the camera's mode could not be read, taken as first person: {error!r}")
        return False
