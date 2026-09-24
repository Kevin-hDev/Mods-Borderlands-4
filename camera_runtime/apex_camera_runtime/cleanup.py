"""Release one owned third-person unit and reset its state only after full success."""

from typing import Any

from . import aiming


def stop(controller: Any, mode: str, transition: str, blend: float, teleport: bool,
         stale: bool = False, now_ns: int | None = None) -> None:
    errors = []
    if controller._hooks_installed:
        try:
            controller._transitions.remove()
            controller._hooks_installed = False
        except Exception as error:
            errors.append(error)
    if controller._mode_pushes:
        try:
            actor, manager = controller._lifetime.owned()
            if actor is not None and manager is not None:
                while controller._mode_pushes:
                    manager.PopActorCameraMode(
                        actor, mode, transition, blend, teleport)
                    controller._mode_pushes -= 1
            else:
                controller._mode_pushes = 0
        except Exception as error:
            if stale:
                controller._mode_pushes = 0
                controller.log("stale third person mode abandoned after map or character change")
            else:
                errors.append(error)
    if controller._bridge_started:
        try:
            controller.bridge.stop()
            controller._bridge_started = False
        except Exception as error:
            errors.append(error)
    if not controller.cleanup_pending:
        controller._remove_cleanup_hook()
        controller._lifetime.clear()
        controller._transitions = None
        controller._in_vehicle = False
        controller._cleanup_attempts = 0
        controller._next_cleanup_ns = 0
        controller._cleanup_stale = False
        controller._disable_cleanup_attempted = False
        controller._recovery_requested = False
        aiming.reset(controller)
        controller._suspensions.clear()
        if controller.collision is not None and hasattr(controller.collision, "reset"):
            controller.collision.reset()
    if errors:
        moment = controller.clock() if now_ns is None else now_ns
        controller._schedule_cleanup(moment, stale)
        raise RuntimeError("third person cleanup incomplete") from errors[0]
