"""Order temporary native climbing before aiming and the selected on-foot camera."""
from . import active_mode, ads_coordination, native_climb_state
from .transitions import VEHICLE_MODE
from .aiming import wants_to_aim


def sync(controller, pc, actor, manager, settings, now_ns):
    try:
        controller.shoulder.configure(controller.bridge, settings)
        orbit_aim = getattr(controller, 'orbit_aim', None)
        if orbit_aim is not None and orbit_aim.busy:
            state = native_climb_state.read(actor)
            if (controller._in_vehicle or str(manager.GetActorCameraMode(actor)) == VEHICLE_MODE
                    or controller.climb.busy or (state is not None and any(state))):
                controller.orbit_aim.interrupt(controller)
        if wants_to_aim(actor):
            cancel = getattr(controller.bridge, 'cancel_orbit_transition', None)
            if callable(cancel):
                cancel(bool(controller._suspensions))
        climbing = controller.climb.sync(controller, pc, actor, manager, now_ns)
        # Climb synchronization can transfer ownership to cleanup in this very frame.
        if not controller._bridge_started or controller.cleanup_retry.pending:
            return
        if controller.anchor is not None:
            controller.anchor.sync(controller, manager,
                                   climbing and controller.climb.phase in ('hold', 'return'))
        if climbing:
            if controller.framing is not None:
                controller.framing.stop()
            controller.zoom.release()
            return
    except Exception:
        controller.stop(now_ns=now_ns)
        raise
    ads_coordination.choose(controller, pc, actor, manager, settings)
    if orbit_aim is None or not orbit_aim.sync(controller, pc, actor, manager, now_ns):
        active_mode.sync(controller, pc, actor, manager, settings, now_ns)
    if controller._bridge_started:
        ads_coordination.confirm(controller, actor, manager)
    if controller.framing is not None:
        controller.framing.sync(controller, pc, actor, manager, settings)
    if controller._bridge_started and not controller.cleanup_retry.pending:
        try:
            controller.zoom.sync(settings)
        except Exception:
            controller.stop(now_ns=now_ns)
            raise
