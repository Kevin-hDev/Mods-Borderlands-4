"""Keep ADS integration separate from camera lifetime and cleanup ownership."""
from .aiming import wants_to_aim


def choose(controller, pc, actor, manager, settings):
    if controller.ads is None:
        return False
    try:
        return controller.ads.prepare(pc, actor, manager, settings,
            foot_mode=controller._desired_mode, vehicle=controller._in_vehicle,
            pending=controller.foot_mode.pending or controller.cleanup_retry.pending)
    except Exception:
        controller.ads.stop()
        controller.ads.feedback.report(None, "unavailable")
        return False


def native_requested(controller):
    actor, manager = controller._lifetime.owned()
    if actor is None or not wants_to_aim(actor):
        return False
    pc = controller._lifetime.pc_ref() if controller._lifetime.pc_ref is not None else None
    return not choose(controller, pc, actor, manager, controller._ads_settings)


def confirm(controller, actor, manager):
    if controller.ads is None:
        return
    try:
        if controller._in_vehicle:
            controller.ads.stop()
            return
        controller.ads.confirm(str(manager.GetActorCameraMode(actor)))
    except Exception:
        controller.ads.stop()
        controller.ads.feedback.report(None, "publication_refused")


def transfer_pending(controller):
    if controller is None:
        return False
    ads = getattr(controller, "ads", None)
    retry = getattr(controller, "cleanup_retry", None)
    return bool(ads is not None and (ads.pending or getattr(retry, "waiting", False)))


def preserve_mode(controller, requested, effective):
    # A redundant Default->ThirdPerson request resets native blend/HUD timing, not just its name.
    if (controller.ads is None or not controller.ads.wanted or controller._mode_pushes != 1
            or controller._in_vehicle or requested != "Default" or effective != "ThirdPerson"):
        return False
    actor, manager = controller._lifetime.owned()
    try:
        return actor is not None and manager is not None and str(manager.GetActorCameraMode(actor)) == effective
    except Exception:
        return False
