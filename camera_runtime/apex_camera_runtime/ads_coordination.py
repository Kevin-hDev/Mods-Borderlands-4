"""Keep ADS integration separate from camera lifetime and cleanup ownership."""
from .aiming import wants_to_aim


def choose(controller, pc, actor, manager, settings):
    if controller.ads is None:
        return False
    try:
        orbit_aim = getattr(controller, 'orbit_aim', None)
        borrow = orbit_aim is not None and orbit_aim.eligible(controller, actor)
        return controller.ads.prepare(pc, actor, manager, settings,
            foot_mode='ThirdPerson' if borrow else controller._desired_mode,
            vehicle=controller._in_vehicle,
            pending=(controller.foot_mode.pending and not borrow) or controller.cleanup_retry.pending)
    except Exception as error:
        controller.ads.stop()
        controller.ads.feedback.exception(None, "preparation_failed", "coordination_prepare", error)
        return False


def native_requested(controller):
    if controller.climb.busy:
        return False
    orbit_aim = getattr(controller, 'orbit_aim', None)
    if orbit_aim is not None and orbit_aim.phase == 'return':
        return False  # Finish the owned return before selecting another aim view.
    actor, manager = controller._lifetime.owned()
    if actor is None or not wants_to_aim(actor):
        return False
    pc = controller._lifetime.pc_ref() if controller._lifetime.pc_ref is not None else None
    wanted = choose(controller, pc, actor, manager, controller._ads_settings)
    if orbit_aim is not None:
        orbit_aim.enter(controller, pc, actor, controller.clock())
    return not wanted or not controller.ads.wanted


def confirm(controller, actor, manager):
    if controller.ads is None:
        return
    try:
        if controller._in_vehicle:
            controller.ads.stop()
            return
        controller.ads.confirm(str(manager.GetActorCameraMode(actor)))
    except Exception as error:
        controller.ads.stop()
        controller.ads.feedback.exception(None, "publication_refused", "coordination_confirm", error)


def transfer_pending(controller):
    if controller is None:
        return False
    ads = getattr(controller, "ads", None)
    retry = getattr(controller, "cleanup_retry", None)
    return bool(ads is not None and (ads.pending or getattr(retry, "waiting", False)))


def preserve_mode(controller, requested, effective):
    # A redundant Default->ThirdPerson request resets native blend/HUD timing, not just its name.
    borrow = getattr(controller, 'orbit_aim', None)
    if (controller.ads is None or not controller.ads.wanted
            or (controller._mode_pushes != 1 and not (borrow is not None and borrow.busy))
            or controller._in_vehicle or requested != "Default" or effective != "ThirdPerson"):
        return False
    actor, manager = controller._lifetime.owned()
    try:
        if borrow is not None and borrow.phase == 'enter':
            return True  # One pending replacement already owns this presentation request.
        return actor is not None and manager is not None and str(manager.GetActorCameraMode(actor)) == effective
    except Exception:
        return False
