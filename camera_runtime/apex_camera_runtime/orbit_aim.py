"""Borrow ThirdPerson for ADS by replacement; Orbit stays the saved return view."""
from .aiming import AIM_BLEND, AIM_FORCE_RESET, AIM_TELEPORT, wants_to_aim
from .constants import CAMERA_TRANSITION, ORBIT_MODE, THIRD_PERSON_MODE
from .foot_mode_rollback import restore
from .orbit_feedback import note_refusal
from .native_climb_state import read as climb_state
from .transitions import VEHICLE_MODE


class OrbitAim:
    def __init__(self):
        self.phase = ''
        self.blocked = False

    @property
    def busy(self):
        return bool(self.phase)

    def mode(self, base):
        if base == ORBIT_MODE and self.phase in ('enter', 'hold'):
            return THIRD_PERSON_MODE
        return base

    def eligible(self, controller, actor):
        if not wants_to_aim(actor):
            self.blocked = False
        state = controller.foot_mode
        own_request = self.phase == 'enter' and state.pending_mode == THIRD_PERSON_MODE
        try:
            _, manager = controller._lifetime.owned()
            climbing = climb_state(actor)
            if (manager is None or str(manager.GetActorCameraMode(actor)) == VEHICLE_MODE
                    or climbing is None or any(climbing)):
                return False
        except Exception:
            return False
        return (not self.blocked and self.phase != 'return'
                and controller._desired_mode == ORBIT_MODE and not controller._in_vehicle
                and not controller._aiming and not controller._aim_returning
                and not controller.climb.busy and not controller.cleanup_retry.pending
                and (not state.pending or own_request) and state.transaction is None)

    def interrupt(self, controller):
        if not self.busy:
            return
        if controller.foot_mode.transaction is None:
            controller.foot_mode.clear_pending()
        self.phase = ''
        self.blocked = True
        controller._suspend('orbit', True)

    def enter(self, controller, pc, actor, now_ns):
        if (controller.ads is None or self.busy or not self.eligible(controller, actor)
                or not controller.ads.wanted):
            return
        controller.offset.release()
        self.phase = 'enter'  # Hooks must see the temporary destination before the call.
        try:
            # A normal mode blend outlasts the weapon zoom and misses the natural HUD update.
            call = lambda mode: pc.CameraTransition(mode, CAMERA_TRANSITION,
                                                    AIM_BLEND, AIM_TELEPORT, AIM_FORCE_RESET)
            accepted = controller.foot_mode.issue(call, THIRD_PERSON_MODE, now_ns)
        except Exception:
            self._native_fallback(controller)
            return
        if not accepted:
            self._native_fallback(controller)

    def _native_fallback(self, controller):
        self.interrupt(controller)
        controller.ads.stop()
        controller.log('Orbit aim view refused; native aiming retained.')

    def sync(self, controller, pc, actor, manager, now_ns):
        if not self.busy:
            self.enter(controller, pc, actor, now_ns)
        if not self.busy:
            return False
        state = controller.foot_mode
        mode = str(manager.GetActorCameraMode(actor))
        if self.phase == 'enter':
            if state.observe(mode, now_ns):
                self.phase = 'hold'
                controller._suspend('orbit', False)
            elif state.timed_out:
                self._native_fallback(controller)
                return False
            else:
                return True
        if self.phase == 'hold':
            if controller.ads.wanted:
                return True
            if not controller.ads.stop():
                return True  # HUD ownership must be restored before replacing its view.
            if controller.framing is not None:
                controller.framing.stop()
            if wants_to_aim(actor):
                self.interrupt(controller)
                return False  # A sniper/native aim takes over without an Orbit detour.
            controller._suspend('orbit', True)
            self.phase = 'return'
            if not state.request(pc, ORBIT_MODE, now_ns):
                self._return_refused(controller, now_ns)
            return True
        if self.phase == 'return':
            if state.observe(mode, now_ns):
                self.phase = ''
                if wants_to_aim(actor):
                    from .ads_coordination import choose
                    choose(controller, pc, actor, manager, controller._ads_settings)
                    self.enter(controller, pc, actor, now_ns)
                return self.busy
            if state.timed_out:
                self._return_refused(controller, now_ns)
            return True
        return False

    def _return_refused(self, controller, now_ns):
        self.interrupt(controller)
        controller._orbit_blocked_identity = controller._lifetime.ids
        note_refusal(controller._ads_settings)
        restore(controller.foot_mode, controller, False, now_ns)

    def reset(self):
        self.phase = ''
        self.blocked = False
