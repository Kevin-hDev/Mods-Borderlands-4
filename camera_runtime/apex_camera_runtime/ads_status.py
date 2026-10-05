"""Read-only menu status; game-view claims require a fresh native mode confirmation."""

REASONS = {"unavailable": "unsupported", "preparation_failed": "install_failed",
           "unknown_weapon": "unknown_weapon", "heavy_native": "heavy_native",
           "wrong_thread": "wrong_thread", "reference_unavailable": "mode_unavailable",
           "publication_refused": "install_failed", "cleanup_pending": "cleanup_pending",
           "cleanup_failed": "cleanup_pending", "animation_pending": "cleanup_pending"}
NATIVE_CONFIRMATION = frozenset(("unknown_weapon", "heavy_native", "wrong_thread", "mode_unavailable"))


def notice(controller):
    if controller is None or controller.ads is None:
        return "unsupported"
    ads = controller.ads
    if ads.pending:
        return "cleanup_pending"
    reason = ads.feedback.reason
    if getattr(ads.native, "_prepared", None) is False:
        reason = getattr(ads.native, "reason", None) or "preparation_failed"
    if getattr(ads, "_thread_failed", False):
        reason = "wrong_thread"
    reason = REASONS.get(reason)
    if reason not in NATIVE_CONFIRMATION:
        return reason
    try:
        actor, manager = controller._lifetime.owned()
        if actor is not None and manager is not None and str(manager.GetActorCameraMode(actor)) == "Default":
            return reason
    except Exception:
        # A loading boundary cannot confirm a restored view.
        pass
    return "cleanup_pending"
