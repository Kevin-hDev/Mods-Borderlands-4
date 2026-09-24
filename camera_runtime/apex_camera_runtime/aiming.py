"""Temporarily yield the owned third-person mode to native first-person aiming."""

from typing import Any

AIM_BLEND = 0.0
AIM_TELEPORT = True
AIM_FORCE_RESET = True


def _wants_to_aim(actor: Any) -> bool:
    zoom = getattr(actor, "ZoomState", None)
    return bool(getattr(zoom, "bWantsToZoom", False))


def sync(controller: Any, pc: Any, actor: Any, manager: Any, mode: str, third_person: str,
         transition: str) -> bool:
    if controller._in_vehicle:
        return False
    wants_to_aim = _wants_to_aim(actor)
    if wants_to_aim and not controller._aiming:
        controller._suspend("aim", True)
        controller._transitions.set_first_person_allowed(True)
        try:
            while controller._mode_pushes:
                manager.PopActorCameraMode(actor, third_person, transition, AIM_BLEND, AIM_TELEPORT)
                controller._mode_pushes -= 1
            # ADS must react on this frame: the shared mode's normal blend is visible and delays firing feedback.
            pc.CameraTransition("Default", transition, AIM_BLEND, AIM_TELEPORT, AIM_FORCE_RESET)
        except Exception:
            controller._transitions.set_first_person_allowed(False)
            controller._suspend("aim", False)
            raise
        controller._aiming = True
        controller._aim_returning = False
        controller._recovery_requested = False
        return True
    if wants_to_aim:
        return True
    if controller._aiming:
        controller._transitions.set_first_person_allowed(False)
        try:
            manager.PushActorCameraMode(actor, third_person, transition, AIM_BLEND, AIM_TELEPORT)
        except Exception:
            controller._transitions.set_first_person_allowed(True)
            raise
        controller._mode_pushes = 1
        controller._aiming = False
        controller._aim_returning = True
        controller._recovery_requested = False
        return True
    if controller._aim_returning:
        if mode != third_person:
            return True
        controller._suspend("aim", False)
        controller._aim_returning = False
    return False


def prepare_vehicle(controller: Any, third_person: str, transition: str,
                    blend: float, teleport: bool) -> None:
    if not (controller._aiming or controller._aim_returning):
        return
    if controller._aiming and not controller._mode_pushes:
        actor, manager = controller._lifetime.owned()
        if actor is None or manager is None:
            raise RuntimeError("camera owner unavailable during vehicle transition")
        manager.PushActorCameraMode(actor, third_person, transition, blend, teleport)
        controller._mode_pushes = 1
    controller._transitions.set_first_person_allowed(False)
    controller._aiming = controller._aim_returning = False
    controller._suspend("aim", False)


def prepare_observed_vehicle(controller: Any) -> None:
    if not (controller._aiming or controller._aim_returning):
        return
    controller._transitions.set_first_person_allowed(False)
    controller._aiming = controller._aim_returning = False
    controller._suspend("aim", False)


def reset(controller: Any) -> None:
    controller._aiming = controller._aim_returning = False
