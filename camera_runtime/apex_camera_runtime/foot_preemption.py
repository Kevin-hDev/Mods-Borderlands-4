"""Cancel any unfinished foot-mode request when ADS or a vehicle takes priority."""

from . import mode_layers
from .constants import ORBIT_MODE, THIRD_PERSON_MODE
from .foot_mode_rollback import restore


def cancel(state, controller, priority: str, restore_layers: bool) -> bool:
    transaction = state.transaction
    if not state.pending or priority not in ("aim", "vehicle", "climb"):
        return False
    if transaction is None:
        requested_mode = state.pending_mode
        restore_orbit = controller._desired_mode == ORBIT_MODE
    else:
        enabled, previous = transaction
        requested_mode = ORBIT_MODE if enabled else state.origin(controller._ads_settings)
        restore_orbit = previous
    actor, manager = controller._lifetime.owned()
    try:
        if restore_orbit:
            if restore_layers and actor is not None and manager is not None:
                mode_layers.remove_all(controller, actor, manager)
            controller.set_desired_mode(ORBIT_MODE)
        else:
            base = state.origin(controller._ads_settings)
            controller.set_desired_mode(base)
            if (restore_layers and actor is not None and manager is not None
                    and not controller._mode_pushes and base == THIRD_PERSON_MODE):
                mode_layers.push_one(controller, actor, manager)
    except Exception as error:
        state.clear_pending()
        state.rollback_failed = True
        try:
            controller.stop()
        except Exception as cleanup_error:
            raise RuntimeError("camera preemption cleanup incomplete") from cleanup_error
        raise RuntimeError("camera preemption failed") from error
    state.clear_pending()
    state.preempted = priority
    state.preempted_mode = requested_mode
    return True


def end(state, priority: str) -> None:
    if state.preempted == priority:
        state.preempted = ""
        state.preempted_mode = ""


def cancel_choice(state, controller, now_ns: int) -> bool:
    transaction = state.transaction
    if transaction is None:
        return False
    restore(state, controller, transaction[1], now_ns)
    # Acknowledgement concerns revoked persistence, not a promise of restored geometry.
    return state.transaction is None
