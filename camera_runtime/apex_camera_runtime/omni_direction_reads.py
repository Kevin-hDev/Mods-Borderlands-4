"""What the omni direction unit reads at each tick: the elected mod's values, Omni Sprint's own switch, the played
body and the view the game shows."""

from typing import Any

from .constants import ORBIT_MODE, THIRD_PERSON_MODE


def wanted_values(settings: Any) -> Any:
    """The elected mod's OMNI DIRECTION values; None from a mod older than this unit."""
    read = getattr(settings, "omni_direction", None)
    return read() if callable(read) else None


def sprint_everywhere(clients: Any) -> bool:
    """Omni Sprint's own switch, whichever mod is elected (Kevin: its switch stays its own)."""
    for client in clients:
        read = getattr(client.settings, "sprint_everywhere", None)
        if callable(read) and read() is True:
            return True
    return False


def played_address(pc: Any) -> int:
    """The address of the played body's animation, 0 without one."""
    character = getattr(pc, "OakCharacter", None) if pc is not None else None
    mesh = getattr(character, "Mesh", None) if character is not None else None
    body = mesh.GetAnimInstance() if mesh is not None else None
    return int(body._get_address()) if body is not None else 0


def in_third_person(controller: Any) -> bool:
    """The view the game shows: third person on foot, not at the wheel, not Orbit, not climbing."""
    if (controller is None or getattr(controller, "_in_vehicle", False)
            or getattr(controller, "_desired_mode", None) == ORBIT_MODE
            or getattr(getattr(controller, "climb", None), "busy", False)):
        return False
    actor, manager = controller._lifetime.owned()
    return actor is not None and manager is not None and str(manager.GetActorCameraMode(actor)) == THIRD_PERSON_MODE
