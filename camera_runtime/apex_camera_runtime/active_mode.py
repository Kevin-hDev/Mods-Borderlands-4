"""Synchronize one active on-foot camera unit after its lifetime is stable."""

from typing import Any

from . import aiming, foot_preemption, mode_layers
from .constants import ORBIT_MODE
from .foot_mode import CONFIRMATION_TIMEOUT_NS
from .orbit_feedback import note_refusal
from .transitions import RECOVERABLE_MODES, THIRD_PERSON, VEHICLE_MODE


def available(controller: Any) -> bool:
    ads = getattr(controller, "ads", None)
    if ads is not None and ads.pending:
        return False
    if (not controller.cleanup_pending or controller.foot_mode.pending or controller._recovery_requested
            or controller._aiming or controller._aim_returning or controller._in_vehicle):
        return False
    actor, manager = controller._lifetime.owned()
    try:
        mode = str(manager.GetActorCameraMode(actor))
    except Exception:
        return False
    return mode == controller._desired_mode and (
        (mode == ORBIT_MODE and controller._mode_pushes == 0)
        or (mode == THIRD_PERSON and controller._mode_pushes == 1))


def _request_recovery(controller: Any, pc: Any, actor: Any,
                      manager: Any, now_ns: int) -> bool:
    state = controller.foot_mode
    target = controller._desired_mode
    if not state.begin(target, now_ns):
        controller.stop(now_ns=now_ns)
        return False
    try:
        mode_layers.remove_all(controller, actor, manager)
        if target == ORBIT_MODE:
            pc.ClientSetCameraMode(ORBIT_MODE)
        else:
            mode_layers.push_one(controller, actor, manager)
    except Exception:
        state.clear_pending()
        controller.stop(now_ns=now_ns)
        raise
    return True


def _settle_request(controller: Any, settings: Any, pc: Any, actor: Any,
                    manager: Any, mode: str, now_ns: int) -> bool:
    state = controller.foot_mode
    if state.transaction is not None:
        state.settle(controller, settings, mode, now_ns)
        if state.rollback_failed:
            controller.stop(now_ns=now_ns)
        return True
    if not state.pending:
        return False
    confirmed = state.observe(mode, now_ns)
    if state.rollback_failed:
        controller.stop(now_ns=now_ns)
        return True
    if state.pending:
        return True
    if state.timed_out and controller._desired_mode == ORBIT_MODE:
        controller._orbit_blocked_identity = controller._lifetime.ids
        controller.set_desired_mode(THIRD_PERSON)
        note_refusal(settings)
        _request_recovery(controller, pc, actor, manager, now_ns)
        return True
    if state.timed_out:
        controller.stop(now_ns=now_ns)
        return True
    if confirmed:
        controller.confirm_desired_mode()
    return False


def sync(controller: Any, pc: Any, actor: Any, manager: Any,
         settings: Any, now_ns: int) -> None:
    mode = str(manager.GetActorCameraMode(actor))
    if controller.foot_mode.pending:
        if aiming.wants_to_aim(actor):
            controller._suspend("aim", True)
            foot_preemption.cancel(controller.foot_mode, controller, "aim", False)
        elif mode == VEHICLE_MODE or controller._in_vehicle:
            controller._suspend("vehicle", True)
            foot_preemption.cancel(
                controller.foot_mode, controller, "vehicle", mode != VEHICLE_MODE)
    if _settle_request(controller, settings, pc, actor, manager, mode, now_ns):
        return
    if mode == VEHICLE_MODE:
        if not controller._in_vehicle:
            controller._suspend("vehicle", True)
            aiming.prepare_observed_vehicle(controller)
        controller._in_vehicle = True
        controller._recovery_requested = False
        controller._suspend("vehicle", True)
        controller._vehicle_reassert_ns = 0
    elif (controller._in_vehicle
          and controller.foot_mode.preempted == "vehicle"
          and (controller._vehicle_reassert_ns
               or mode == controller.foot_mode.preempted_mode)):
        if (controller._vehicle_reassert_ns
                and now_ns - controller._vehicle_reassert_ns > CONFIRMATION_TIMEOUT_NS):
            controller.stop(now_ns=now_ns)
            return
        if not controller._vehicle_reassert_ns:
            try:
                pc.ClientSetCameraMode(VEHICLE_MODE)
            except Exception:
                controller.stop(now_ns=now_ns)
                raise
            controller._vehicle_reassert_ns = now_ns or 1
        return
    elif controller._in_vehicle and mode == controller._desired_mode:
        was_preempted = controller.foot_mode.preempted == "vehicle"
        foot_preemption.end(controller.foot_mode, "vehicle")
        controller._in_vehicle = False
        controller._recovery_requested = False
        controller._suspend("vehicle", False)
        if was_preempted and controller._desired_mode == ORBIT_MODE and controller._mode_pushes:
            mode_layers.remove_all(controller, actor, manager)
            controller.foot_mode.request(pc, ORBIT_MODE, now_ns)
            return
        if not controller._mode_pushes:
            return
    elif aiming.sync(controller, pc, actor, manager, mode, THIRD_PERSON,
                      controller._desired_mode, controller.transition_name, now_ns):
        return
    elif mode == controller._desired_mode:
        controller.foot_mode.observe(mode, now_ns)
        controller._in_vehicle = False
        controller._recovery_requested = False
        controller._suspend("vehicle", False)
    elif (mode in RECOVERABLE_MODES
          and mode != controller._desired_mode and not controller._in_vehicle
          and not controller._recovery_requested):
        controller._recovery_requested = _request_recovery(
            controller, pc, actor, manager, now_ns)
        if controller._recovery_requested:
            controller.foot_mode.restorations += 1
    if controller.collision is not None and "vehicle" not in controller._suspensions:
        controller.collision.sample(
            now_ns, actor, controller.bridge,
            lambda blocked: controller._suspend("collision", blocked))
