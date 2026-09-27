"""One confirmed transaction for the elected on-foot camera mode."""

from . import mode_layers
from .constants import ORBIT_MODE, THIRD_PERSON_MODE
from .foot_mode_rollback import restore
from .orbit_feedback import note_refusal, note_save_failure

RESTORE_EXPECTED_NS = 300_000_000
CONFIRMATION_TIMEOUT_NS = 800_000_000
ALLOWED_MODES = frozenset((ORBIT_MODE, THIRD_PERSON_MODE))


class FootModeState:
    def __init__(self) -> None:
        self.pending_mode = ""
        self.requested_ns = 0
        self.pending_choice = None
        self.previous_choice = None
        self.pending_rollback = False
        self.rollback_failed = False
        self.preempted = ""
        self.preempted_mode = ""
        self.timed_out = False
        self.requests = 0
        self.confirmations = 0
        self.restorations = 0
        self.refusals = 0

    @property
    def pending(self) -> bool:
        return bool(self.pending_mode)

    @property
    def transaction(self):
        if self.pending_choice is None:
            return None
        return self.pending_choice, self.previous_choice

    def desired(self, settings: object) -> str:
        try:
            enabled = settings.orbit_enabled()
        except Exception:
            return THIRD_PERSON_MODE
        return ORBIT_MODE if enabled is True else THIRD_PERSON_MODE

    def begin(self, mode: str, now_ns: int, choice=None, previous=None,
              rollback: bool = False) -> bool:
        valid_choice = (choice is None and previous is None) or (
            type(choice) is bool and type(previous) is bool)
        if (type(mode) is not str or mode not in ALLOWED_MODES or type(now_ns) is not int
                or now_ns < 0 or self.pending or not valid_choice
                or type(rollback) is not bool):
            self.refusals += 1
            return False
        self.pending_mode = mode
        self.requested_ns = now_ns
        self.pending_choice = choice
        self.previous_choice = previous
        self.pending_rollback = rollback
        self.rollback_failed = False
        if not rollback:
            self.timed_out = False
        self.requests += 1
        return True

    def request(self, pc: object, mode: str, now_ns: int,
                choice=None, previous=None, rollback: bool = False) -> bool:
        if not self.begin(mode, now_ns, choice, previous, rollback):
            return False
        try:
            pc.ClientSetCameraMode(mode)
        except Exception:
            self._clear_pending()
            self.refusals += 1
            return False
        return True

    def issue(self, call: object, mode: str, now_ns: int) -> bool:
        if not self.begin(mode, now_ns):
            return False
        try:
            call(mode)
        except Exception:
            self._clear_pending()
            self.refusals += 1
            raise
        return True

    def observe(self, effective_mode: str, now_ns: int) -> bool:
        if not self.pending:
            return False
        if effective_mode == self.pending_mode:
            rollback = self.pending_rollback
            self._clear_pending()
            if rollback:
                self.rollback_failed = False
                self.timed_out = False
            self.confirmations += 1
            return True
        if type(now_ns) is int and now_ns - self.requested_ns > CONFIRMATION_TIMEOUT_NS:
            rollback = self.pending_rollback
            self._clear_pending()
            self.timed_out = True
            self.rollback_failed = rollback
            self.refusals += 1
        return False

    def set_orbit(self, controller: object, settings: object,
                  enabled: bool, now_ns: int) -> bool:
        if type(enabled) is not bool or not controller.orbit_available():
            return False
        pc = controller._lifetime.pc_ref() if controller._lifetime.pc_ref is not None else None
        actor, manager = controller._lifetime.owned()
        if pc is None or actor is None or manager is None:
            return False
        try:
            previous = settings.orbit_enabled()
        except Exception:
            return False
        if type(previous) is not bool:
            return False
        blocked = controller._orbit_blocked_identity == controller._lifetime.ids
        if enabled == previous and not (enabled and blocked):
            return False
        if not enabled and blocked:
            try:
                settings.set_orbit(False)
            except Exception:
                return False
            controller._orbit_blocked_identity = None
            return True
        target = ORBIT_MODE if enabled else THIRD_PERSON_MODE
        if not self.begin(target, now_ns, enabled, previous):
            return False
        try:
            if enabled:
                mode_layers.remove_all(controller, actor, manager)
                controller.set_desired_mode(ORBIT_MODE)
                pc.ClientSetCameraMode(ORBIT_MODE)
                controller._orbit_blocked_identity = None
            else:
                mode_layers.push_one(controller, actor, manager)
                # Orbit remains on screen until the game confirms this request.
                controller.set_desired_mode(THIRD_PERSON_MODE, release_orbit=False)
        except Exception:
            self._clear_pending()
            note_refusal(settings)
            restore(self, controller, previous, now_ns)
            return False
        return True

    def settle(self, controller: object, settings: object,
               effective_mode: str, now_ns: int) -> bool:
        transaction = self.transaction
        if transaction is None:
            return False
        confirmed = self.observe(effective_mode, now_ns)
        if not confirmed and not self.timed_out:
            return True
        enabled, previous = transaction
        if confirmed:
            try:
                settings.set_orbit(enabled)
                controller._orbit_blocked_identity = None
                controller.confirm_desired_mode()
                return True
            except Exception:
                note_save_failure(settings)
        else:
            note_refusal(settings)
            reject = getattr(settings, "reject_orbit", None)
            if callable(reject):
                reject()
        restore(self, controller, previous, now_ns)
        return True

    def toggle_orbit(self, controller: object, settings: object, now_ns: int) -> bool:
        try:
            enabled = settings.orbit_enabled()
        except Exception:
            return False
        target = not enabled
        return self.set_orbit(controller, settings, target, now_ns)

    def _clear_pending(self) -> None:
        self.pending_mode = ""
        self.requested_ns = 0
        self.pending_choice = None
        self.previous_choice = None
        self.pending_rollback = False

    def clear_pending(self) -> None:
        self._clear_pending()

    def reset(self) -> None:
        self._clear_pending()
        self.timed_out = False
        self.rollback_failed = False
        self.preempted = ""
        self.preempted_mode = ""
