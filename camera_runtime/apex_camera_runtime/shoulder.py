"""Transactional left/right shoulder state backed by the elected owner's settings."""

from typing import Any

from .constants import THIRD_PERSON_MODE, THIRD_PERSON_RIGHT
from .shoulder_auto import CLEAR, AutoShoulder, swap_due
from .shoulder_sight import ShoulderSight

# A long frame counts as this much, so a hitch never completes a swap's delay on its own.
MAX_STEP_S = 0.1


def signed_right(left: bool) -> float:
    if type(left) is not bool:
        raise ValueError("invalid shoulder side")
    return -THIRD_PERSON_RIGHT if left else THIRD_PERSON_RIGHT


def _values(settings: Any):
    """The switch and its delays, or None for a mod from before them (2026-10-07): it has no way to turn the switch
    off, so it never switches."""
    read = getattr(settings, "shoulder_auto", None)
    return read() if callable(read) else None


def _share(value: float | None) -> str:
    return "unread" if value is None else f"{value:.2f}"


def _met(seen: str) -> str:
    """What cut a side's room, in brackets; nothing when it was not swept again (shoulder_clearance.py)."""
    return f" ({seen})" if seen else ""


class ShoulderState:
    def __init__(self) -> None:
        self.auto = AutoShoulder()
        # The side given to the native camera, which can differ from the saved one during a swap.
        self.shown_left: bool | None = None
        self.last_ns: int | None = None
        self.sight: ShoulderSight | None = None
        self.sight_failed = False
        # Each side's room and view ahead behind the last shares, written with a swap.
        self.measured = ""
        # An opening kept the shown side last frame: the log names the first frame of each such stretch only.
        self.kept = False

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
        self.auto.reset()
        self.shown_left = self.last_ns = None
        try:
            left = settings.shoulder_left()
            if not bridge.set_right(signed_right(left)):
                return False
        except Exception:
            return False
        self.shown_left = left
        return True

    def follow(self, controller: Any, settings: Any, now_ns: int) -> None:
        """Show the other shoulder while a wall takes the chosen one's room or view (shoulder_auto.py)."""
        seconds = 0.0 if self.last_ns is None else min(MAX_STEP_S, max(0.0, (now_ns - self.last_ns) / 1e9))
        self.last_ns = now_ns
        collision = getattr(controller.bridge, "collision", None)
        clearance = getattr(collision, "clearance", None)
        if clearance is None or self.shown_left is None:
            return
        reading = clearance.take()
        if reading is None:
            # The camera guard is not measuring (aiming, vehicle, Orbit...): hold the side shown.
            clearance.wanted = clearance.active = False
            self.auto.step(settings.shoulder_left(), None, None, False, seconds)
            return
        allowed = self.available(controller)
        values = _values(settings)
        if values is None or not values.enabled:
            clearance.wanted = clearance.active = False
            self._show_chosen(controller, settings, allowed)
            return
        shown, other = self._shares(controller, collision, reading) if allowed else (reading.room, None)
        side = self.auto.step(settings.shoulder_left(), shown, other, allowed, seconds, values.swap_s, values.return_s)
        clearance.wanted = allowed and (self.auto.override is not None or shown < CLEAR)
        clearance.active = allowed
        if side is self.shown_left or not allowed:
            return
        self.configure(controller.bridge, settings)
        if not controller.bridge.set_right(signed_right(side)):
            raise RuntimeError("automatic shoulder refused")
        self.shown_left = side
        controller.log(f"automatic shoulder: {'left' if side else 'right'} shown "
                       f"(free {_share(shown)}, other {_share(other)}){self.measured}")

    def _show_chosen(self, controller: Any, settings: Any, allowed: bool) -> None:
        """Switched off in the menu: a swap under way ends at once."""
        self.auto.reset()
        left = settings.shoulder_left()
        if left is self.shown_left or not allowed:
            return
        self.configure(controller.bridge, settings)
        if not controller.bridge.set_right(signed_right(left)):
            raise RuntimeError("automatic shoulder refused")
        self.shown_left = left
        controller.log(f"automatic shoulder: switched off, {'left' if left else 'right'} shown")

    def _shares(self, controller: Any, collision: Any, reading: Any) -> tuple:
        """Each side's free share: the smaller of its room and its view ahead, and of the view past an opening when only
        the view would swap."""
        shown, other = reading.room, reading.other_room
        self.measured = ""
        if self.sight_failed:
            return shown, other
        try:
            if self.sight is None:
                self.sight = ShoulderSight(collision.sweep.kismet, collision.sweep.sdk)
            actor, manager = controller._lifetime.owned()
            yaw = float(manager.GetCameraRotation().Yaw)
            view = self.sight.share(actor, reading.camera, yaw)
            self.measured = f"; shown room {_share(shown)}{_met(reading.seen)} view {_share(view)} {self.sight.seen}"
            shown = min(shown, view)
            kept = False
            if other is not None and reading.other_camera is not None:
                view = self.sight.share(actor, reading.other_camera, yaw)
                self.measured += (f"; other room {_share(other)}{_met(reading.other_seen)} view {_share(view)} "
                                  f"{self.sight.seen}")
                other = min(other, view)
                if (self.auto.override is None and not self.auto.waiting and swap_due(shown, other)
                        and not swap_due(reading.room, other)):
                    # Only the view ahead asks for this swap: the other side must see on past the door or window it
                    # looks through (shoulder_sight.py). A camera squeezed by a wall still swaps on its room alone.
                    beyond = self.sight.opening(actor, reading.camera, reading.other_camera, yaw)
                    self.measured += f"; beyond {_share(beyond)} {self.sight.seen}"
                    other = min(other, beyond)
                    kept = other < CLEAR
            if kept and not self.kept:
                controller.log(f"automatic shoulder: {'left' if self.shown_left else 'right'} kept, the other side "
                               f"only sees through an opening{self.measured}")
            self.kept = kept
        except Exception as error:
            # The view ahead is comfort: without it, the swap still answers a wall at the camera.
            self.sight_failed, self.measured = True, ""
            controller.log(f"automatic shoulder: view ahead unavailable ({type(error).__name__}), room only")
            return reading.room, reading.other_room
        return shown, other

    def player_switch(self, controller: Any, settings: Any) -> bool:
        """The shoulder key during a swap: show the chosen shoulder again, the saved one unchanged."""
        if self.auto.override is None or not self.available(controller):
            return False
        left = settings.shoulder_left()
        self.configure(controller.bridge, settings)
        if not controller.bridge.set_right(signed_right(left)):
            return False
        self.auto.player_switch()
        self.shown_left = left
        return True

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
            self.auto.reset()
            self.shown_left = new_left
        except Exception:
            try:
                restored = bridge.set_right(old_right)
            except Exception:
                restored = False
            if not restored:
                raise RuntimeError("shoulder rollback refused")
            self.auto.reset()
            self.shown_left = old_left
            return False
        return True
