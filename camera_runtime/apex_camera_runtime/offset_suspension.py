"""Only pure climb/Orbit can blend offsets; stronger owners cancel immediately."""
from .constants import ORBIT_MODE, THIRD_PERSON_MODE


def orbit_permission(controller, identity, entering=False):
    def allowed(manager, actor):
        owned_actor, owned_manager = controller._lifetime.owned()
        address = controller._lifetime.address
        return (controller._bridge_started and controller._lifetime.ids == identity
                and owned_actor is not None and owned_manager is not None
                and address(actor) == address(owned_actor)
                and address(manager) == address(owned_manager)
                and controller._suspensions <= {'orbit'}
                and not controller._aiming and not controller._in_vehicle
                and not controller.climb.busy
                and actor.ZoomState.bWantsToZoom is False
                and str(manager.GetActorCameraMode(actor)) in (
                    ('Default', THIRD_PERSON_MODE) if entering else (ORBIT_MODE, THIRD_PERSON_MODE)))
    return allowed


def suspend(controller, reason, enabled):
    previous = controller._suspensions.copy()
    controller._suspensions.add(reason) if enabled else controller._suspensions.discard(reason)
    current = controller._suspensions
    before, after = bool(previous), bool(current)
    was_climb, is_climb = previous == {'climb'}, current == {'climb'}
    was_orbit, is_orbit = previous == {'orbit'}, current == {'orbit'}
    changed = (before != after
               or (was_climb != is_climb and hasattr(controller.bridge, 'suspend_climb'))
               or (was_orbit != is_orbit and hasattr(controller.bridge, 'suspend_orbit')))
    if not controller._bridge_started or not changed:
        return
    try:
        if is_climb or (was_climb and not after):
            getattr(controller.bridge, 'suspend_climb', controller.bridge.suspend)(after)
        elif is_orbit or (was_orbit and not after):
            blend = getattr(controller.bridge, 'suspend_orbit', None)
            settings = controller._ads_settings
            duration = getattr(settings, 'orbit_transition', lambda: 0.0)()
            if callable(blend):
                blend(after, duration, orbit_permission(controller, controller._lifetime.ids))
            else:
                controller.bridge.suspend(after)
        else:
            controller.bridge.suspend(after)
    except Exception:
        controller._suspensions = previous
        raise
