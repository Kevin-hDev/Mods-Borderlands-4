"""Transactional left/right shoulder state backed by the elected owner's settings."""

from typing import Any

from .constants import THIRD_PERSON_MODE, THIRD_PERSON_RIGHT


def signed_right(left: bool) -> float:
    if type(left) is not bool:
        raise ValueError("invalid shoulder side")
    return -THIRD_PERSON_RIGHT if left else THIRD_PERSON_RIGHT


class ShoulderState:
    @staticmethod
    def configure(bridge, settings):
        timing = getattr(settings, 'shoulder_transition', None)
        if timing is not None:
            bridge.transition_duration(timing())

    def available(self, controller: Any) -> bool:
        if getattr(getattr(controller, "climb", None), "busy", False):
            return False
        ads = getattr(controller, "ads", None)
        if ads is not None and (ads.pending or (ads.wanted and not ads.effective)):
            return False
        if not (controller._bridge_started and controller._hooks_installed
                and controller._mode_pushes > 0 and not controller._aiming
                and not controller._in_vehicle and not controller.foot_mode.pending):
            return False
        actor, manager = controller._lifetime.owned()
        try:
            return actor is not None and manager is not None and str(
                manager.GetActorCameraMode(actor)) == THIRD_PERSON_MODE
        except Exception:
            return False

    def apply_saved(self, bridge: Any, settings: Any) -> bool:
        try:
            return bool(bridge.set_right(signed_right(settings.shoulder_left())))
        except Exception:
            return False

    def set(self, bridge: Any, settings: Any, new_left: bool) -> bool:
        if type(new_left) is not bool:
            return False
        try:
            old_left = settings.shoulder_left()
            if type(old_left) is not bool or old_left is new_left:
                return False
            old_right = signed_right(old_left)
            self.configure(bridge, settings)
            if not bridge.set_right(signed_right(new_left)):
                return False
        except Exception:
            return False
        try:
            settings.set_shoulder_left(new_left)
        except Exception:
            try:
                restored = bridge.set_right(old_right)
            except Exception:
                restored = False
            if not restored:
                raise RuntimeError("shoulder rollback refused")
            return False
        return True
