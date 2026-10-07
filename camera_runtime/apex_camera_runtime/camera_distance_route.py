"""The camera distance key, accepted from the elected owner only, on foot in third person."""

from typing import Any

from .camera_distance import NAMES, following
from .constants import ORBIT_MODE, THIRD_PERSON_MODE


def cycle(runtime: Any, owner: str) -> bool:
    client = runtime.arbiter.active()
    controller = runtime.third_person
    if client is None or client.owner != owner or controller is None:
        return False
    settings = client.settings
    # A mod older than the key has neither; its own runtime copy never calls this.
    read, save = getattr(settings, "camera_distance", None), getattr(settings, "set_camera_distance", None)
    if not (callable(read) and callable(save)):
        return False
    try:
        if not (settings.third_person_enabled() and _available(controller)):
            return False
        index = following(read())
        save(index)
    except Exception:
        settings.note("camera distance shortcut: setting could not be saved")
        return False
    controller.log(f"camera distance {NAMES[index]}")
    return True


def _available(controller: Any) -> bool:
    if (not controller.offset.ready() or controller._in_vehicle or controller._desired_mode == ORBIT_MODE
            or controller.foot_mode.pending):
        return False
    actor, manager = controller._lifetime.owned()
    return actor is not None and manager is not None and str(manager.GetActorCameraMode(actor)) == THIRD_PERSON_MODE
