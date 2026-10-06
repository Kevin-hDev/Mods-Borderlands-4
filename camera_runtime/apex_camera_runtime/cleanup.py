"""Release one owned third-person unit and reset its state only after full success."""

from typing import Any

from . import aiming


def stop(controller: Any, mode: str, transition: str, blend: float, teleport: bool,
         stale: bool = False, now_ns: int | None = None) -> None:
    errors = []
    if controller.anchor is not None:
        try:
            controller.anchor.stop()
        except Exception as error:
            errors.append(error)
    if controller.framing is not None:
        try:
            controller.framing.stop()
        except Exception as error:
            errors.append(error)
    if controller.ads is not None and not controller.ads.stop():
        moment = controller.clock() if now_ns is None else now_ns
        controller.cleanup_retry.schedule_wait(controller, moment, stale)
        return
    try:
        controller.zoom.stop(stale=stale)
    except Exception as error:
        errors.append(error)
    if controller._hooks_installed:
        try:
            controller._transitions.remove()
            controller._hooks_installed = False
        except Exception as error:
            errors.append(error)
    # A cancelled FP entry owns no layer: yielding must not replace a stronger native view.
    yield_native = (controller._desired_mode == transition and not controller._mode_pushes
                    and (controller._in_vehicle or controller._aiming or controller.climb.busy))
    controller.foot_mode.reset()
    try:
        pc = controller._lifetime.pc_ref() if controller._lifetime.pc_ref is not None else None
        if not yield_native and pc is not None and callable(getattr(pc, "ClientSetCameraMode", None)):
            # Default is requested after hook removal so shutdown has one native end state.
            pc.ClientSetCameraMode(transition)
    except Exception as error:
        controller.foot_mode.rollback_failed = True
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
        controller.cleanup_retry.reset()
        controller._lifetime.clear()
        controller._transitions = None
        controller._in_vehicle = False
        controller._vehicle_reassert_ns = 0
        controller._recovery_requested = False
        aiming.reset(controller)
        controller.climb.reset()
        orbit_aim = getattr(controller, 'orbit_aim', None)
        if orbit_aim is not None:
            orbit_aim.reset()
        controller._suspensions.clear()
    if errors:
        moment = controller.clock() if now_ns is None else now_ns
        controller.cleanup_retry.schedule(controller, moment, stale)
        raise RuntimeError("third person cleanup incomplete") from errors[0]
