"""Restore the last saved foot mode after a refused transition or save."""

from . import mode_layers
from .constants import ORBIT_MODE, THIRD_PERSON_MODE


def restore(state, controller, orbit: bool, now_ns: int) -> None:
    """Begin one tracked rollback; its caller observes confirmation on later frames."""
    pc = controller._lifetime.pc_ref() if controller._lifetime.pc_ref is not None else None
    actor, manager = controller._lifetime.owned()
    if pc is None or actor is None or manager is None:
        return
    state.clear_pending()
    if orbit:
        try:
            mode_layers.remove_all(controller, actor, manager)
            controller.set_desired_mode(ORBIT_MODE)
            accepted = state.request(pc, ORBIT_MODE, now_ns, rollback=True)
        except Exception:
            accepted = False
        if not accepted:
            state.clear_pending()
            state.rollback_failed = True
        return
    # Orbit can still be visible here: release its native suspension only after ThirdPerson is observed.
    controller.set_desired_mode(THIRD_PERSON_MODE, release_orbit=False)
    if not state.begin(THIRD_PERSON_MODE, now_ns, rollback=True):
        state.rollback_failed = True
        return
    try:
        if not controller._mode_pushes:
            mode_layers.push_one(controller, actor, manager)
    except Exception:
        state.clear_pending()
        state.rollback_failed = True
