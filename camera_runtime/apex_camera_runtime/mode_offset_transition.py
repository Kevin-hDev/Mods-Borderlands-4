"""Animate only a player's mode toggle; resource cleanup remains immediate."""
from .constants import THIRD_PERSON_MODE
from . import native_climb_state
from .offset_suspension import orbit_permission


def duration(settings):
    return getattr(settings, 'orbit_transition', lambda: 0.0)()


class ModeOffsetTransition:
    def __init__(self):
        self.deadline = None

    def cancel(self):
        self.deadline = None

    @staticmethod
    def _safe(controller, pc, entering=False):
        if pc is None or not controller._bridge_started:
            return False
        _, actor, manager, _, changed = controller._lifetime.inspect(pc)
        if changed or controller._suspensions or controller.climb.busy:
            return False
        if (not controller._hooks_installed or not controller._mode_pushes
                or controller.cleanup_retry.pending or controller.cleanup_retry.exhausted):
            return False
        if controller._aiming or controller._aim_returning or controller._in_vehicle:
            return False
        if controller.foot_mode.transaction is not None:
            return False
        traversal = native_climb_state.read(actor)
        if traversal is None or any(traversal):
            return False
        modes = ('Default', THIRD_PERSON_MODE) if entering else (THIRD_PERSON_MODE,)
        return (actor.ZoomState.bWantsToZoom is False
                and str(manager.GetActorCameraMode(actor)) in modes)

    @staticmethod
    def _blend(controller, suspended, seconds, entering=False):
        base = orbit_permission(controller, controller._lifetime.ids, entering=entering)
        def permission(manager, actor):
            pc = controller._lifetime.pc_ref()
            return ModeOffsetTransition._safe(controller, pc, entering) and base(manager, actor)
        controller.bridge.suspend_orbit(suspended, seconds, permission)

    def enter(self, controller, pc, settings):
        seconds = duration(settings)
        if (seconds and hasattr(controller.bridge, 'suspend_orbit')
                and self._safe(controller, pc, entering=True)):
            # Start from zero added offset; leave the native mode's blend untouched.
            controller.bridge.suspend(True)
            self._blend(controller, False, seconds, entering=True)

    def sync(self, controller, pc, settings, enabled, now_ns):
        if self.deadline is None and enabled:
            return False
        seconds = duration(settings)
        if not seconds or not self._safe(controller, pc):
            self.cancel()
            return False
        if enabled:
            self._blend(controller, False, seconds)
            self.cancel()
            return False
        active = getattr(controller.bridge, 'offset_transition_active', None)
        if not callable(active):
            return False
        if self.deadline is None:
            self._blend(controller, True, seconds)
            self.deadline = now_ns + int(seconds * 1_000_000_000)
        elif now_ns >= self.deadline or not active():
            self.cancel()
            return False
        # The native frame hook continues collision-safe centering, not mode rewrites.
        return True
