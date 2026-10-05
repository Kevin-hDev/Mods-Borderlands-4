"""Own the native shift, camera mode and transition hooks as one retryable unit."""

import time
from typing import Any, Callable

from . import active_mode, ads_coordination, aiming, cleanup, foot_preemption, mode_layers
from .cleanup_retry import MAX_CLEANUP_ATTEMPTS, CleanupRetry
from .constants import CAMERA_BLEND as BLEND
from .constants import CAMERA_TELEPORT as TELEPORT
from .constants import CAMERA_TRANSITION as TRANSITION
from .controller_actions import ControllerActions
from .foot_mode import ORBIT_MODE, THIRD_PERSON_MODE, FootModeState
from .lifetime import CameraLifetime
from .orbit_zoom import OrbitZoom
from .orbit_feedback import note_refusal
from .shoulder import ShoulderState, signed_right
from .transitions import THIRD_PERSON, VEHICLE_MODE, TransitionHooks

class ThirdPersonController(ControllerActions):
    def __init__(self, hooks: Any, bridge: Any, identifier: str,
                 weak_ref: Callable | None = None, log: Callable | None = None,
                 clock: Callable[[], int] | None = None, ads: Any = None,
                 framing: Any = None) -> None:
        self.hooks = hooks
        self.bridge = bridge
        self.identifier = identifier
        self.weak_ref = weak_ref or (lambda item: lambda: item)
        self.log = log or (lambda _message: None)
        self.clock = clock or time.perf_counter_ns
        self._lifetime = CameraLifetime(self.weak_ref)
        self._transitions = None
        self._bridge_started = self._hooks_installed = False
        self._mode_pushes = 0
        self.cleanup_retry = CleanupRetry(hooks, identifier, self.clock, self.log)
        self.shoulder = ShoulderState()
        self.foot_mode = FootModeState()
        self._desired_mode = THIRD_PERSON_MODE
        self._orbit_blocked_identity = None
        self._pending_identity = None
        self._recovery_requested = False
        self._in_vehicle = False
        self._vehicle_reassert_ns = 0
        self._aiming = False
        self._aim_returning = False
        self._suspensions: set[str] = set()
        self.transition_name = TRANSITION
        self.zoom = OrbitZoom(self)
        self.ads = ads
        self.framing = framing
        self._ads_settings = None

    @property
    def cleanup_pending(self) -> bool:
        return (self._bridge_started or self._hooks_installed or self._mode_pushes > 0
                or self.foot_mode.rollback_failed or self.zoom.pending
                or (self.ads is not None and self.ads.pending))

    def _suspend(self, reason: str, enabled: bool) -> None:
        previous = self._suspensions.copy()
        before = bool(self._suspensions)
        self._suspensions.add(reason) if enabled else self._suspensions.discard(reason)
        after = bool(self._suspensions)
        if self._bridge_started and before != after:
            try:
                self.bridge.suspend(after)
            except Exception:
                self._suspensions = previous
                raise

    def set_desired_mode(self, mode: str, release_orbit: bool = True) -> None:
        if mode not in (THIRD_PERSON_MODE, ORBIT_MODE):
            raise ValueError("unsupported foot camera mode")
        if mode == ORBIT_MODE or release_orbit:
            self._suspend("orbit", mode == ORBIT_MODE)
        self._desired_mode = mode

    def confirm_desired_mode(self) -> None:
        self._suspend("orbit", self._desired_mode == ORBIT_MODE)

    def _on_transition(self, requested: str, effective: str) -> None:
        if requested == VEHICLE_MODE:
            if self.ads is not None:
                self.ads.stop()
            self._suspend("vehicle", True)
            try:
                foot_preemption.cancel(self.foot_mode, self, "vehicle", True)
                aiming.prepare_vehicle(
                    self, THIRD_PERSON, self._desired_mode, TRANSITION, BLEND, TELEPORT)
            except Exception:
                self._suspend("vehicle", False)
                raise
            self._in_vehicle = True
        elif effective == self._desired_mode:
            self._in_vehicle = False
            self._vehicle_reassert_ns = 0
            foot_preemption.end(self.foot_mode, "vehicle")

    def _start(self, pc: Any, settings: Any, now_ns: int) -> None:
        actor = getattr(pc, "OakCharacter", None)
        manager = getattr(pc, "PlayerCameraManager", None)
        if actor is None or manager is None:
            return
        self._lifetime.bind(pc, actor, manager)
        self.set_desired_mode(self.foot_mode.desired(settings))
        self._recovery_requested = False
        try:
            # Own partial native setup too, so a failed rollback stays in bounded cleanup.
            self._bridge_started = True
            if not self.bridge.start(manager, signed_right(settings.shoulder_left()), pc):
                raise RuntimeError("native camera start refused")
            if self.framing is not None:
                self.framing.diagnostics.rearm()
            if self._suspensions:
                self.bridge.suspend(True)
            if not self.shoulder.apply_saved(self.bridge, settings):
                raise RuntimeError("saved shoulder refused")
            self._transitions = TransitionHooks(
                self.hooks, self.identifier, pc, self.log, self._on_transition,
                lambda: self._desired_mode, self._request_transition,
                lambda: ads_coordination.native_requested(self),
                lambda requested, effective: ads_coordination.preserve_mode(self, requested, effective))
            self._transitions.install()
            self._hooks_installed = True
            if self._desired_mode == ORBIT_MODE:
                if not self.foot_mode.request(pc, ORBIT_MODE, now_ns):
                    self._orbit_blocked_identity = self._lifetime.ids
                    self.set_desired_mode(THIRD_PERSON_MODE)
                    note_refusal(settings)
                    mode_layers.push_one(self, actor, manager)
                else:
                    self.foot_mode.observe(str(manager.GetActorCameraMode(actor)), now_ns)
            else:
                manager.PushActorCameraMode(actor, THIRD_PERSON, TRANSITION, BLEND, TELEPORT)
                self._mode_pushes += 1
        except Exception as setup_error:
            try:
                self.stop()
            except Exception as cleanup_error:
                raise RuntimeError("third person setup cleanup incomplete") from cleanup_error
            raise setup_error

    def sync(self, _owner: str, pc: Any, settings: Any, _now_ns: int) -> None:
        if self.cleanup_retry.waiting:
            self.cleanup_retry.retry(self, _now_ns)
            if self.cleanup_retry.pending:
                return
        self._ads_settings = settings
        enabled = settings.third_person_enabled()
        if not enabled or pc is None:
            if self.cleanup_pending and self.cleanup_retry.exhausted:
                if enabled or self.cleanup_retry.disable_attempted:
                    return
                self.cleanup_retry.disable_attempted = True
                try:
                    self.stop(stale=self.cleanup_retry.stale, now_ns=_now_ns)
                except RuntimeError:
                    self.log("manual third person cleanup failed after bounded retries")
            elif self.cleanup_retry.pending:
                self.cleanup_retry.retry(self, _now_ns)
            else:
                self.stop(now_ns=_now_ns)
            return
        if self.foot_mode.transaction is None:
            desired = self.foot_mode.desired(settings)
            if desired == ORBIT_MODE and self._orbit_blocked_identity == self._lifetime.ids:
                desired = THIRD_PERSON_MODE
            self.set_desired_mode(desired)
        current, actor, _manager, target, changed = self._lifetime.inspect(pc)
        if actor is None and self._in_vehicle and current is not None and target[0] == self._lifetime.ids[0]:
            return
        if changed:
            if target != self._pending_identity:
                self._pending_identity = target
                self.cleanup_retry.reset()
                if target != self._orbit_blocked_identity:
                    self._orbit_blocked_identity = None
            if self.cleanup_pending:
                if self.cleanup_retry.exhausted:
                    return
                if self.cleanup_retry.pending:
                    self.cleanup_retry.retry(self, _now_ns)
                else:
                    self.stop(stale=True, now_ns=_now_ns)
                if self.cleanup_pending:
                    return
            self._pending_identity = None
            self._start(pc, settings, _now_ns)
        elif self.cleanup_pending and self.cleanup_retry.exhausted:
            return
        elif (self.cleanup_pending
              and not (self._bridge_started and self._hooks_installed
                       and (self._mode_pushes > 0 or self._aiming or self._aim_returning
                            or self._in_vehicle or self._desired_mode == ORBIT_MODE))):
            # A re-enable after partial cleanup must rebuild one complete owned unit.
            if self.cleanup_retry.pending:
                self.cleanup_retry.retry(self, _now_ns)
            else:
                self.stop(now_ns=_now_ns)
            if self.cleanup_pending:
                return
            self._start(pc, settings, _now_ns)
        if not self.cleanup_pending:
            return
        actor, manager = self._lifetime.owned()
        if actor is None or manager is None:
            if self.cleanup_retry.pending:
                self.cleanup_retry.retry(self, _now_ns)
            else:
                self.stop(stale=True, now_ns=_now_ns)
            return
        ads_coordination.choose(self, pc, actor, manager, settings)
        active_mode.sync(self, pc, actor, manager, settings, _now_ns)
        if self._bridge_started:
            ads_coordination.confirm(self, actor, manager)
        if self.framing is not None:
            self.framing.sync(self, pc, actor, manager, settings)
        if self._bridge_started and not self.cleanup_retry.pending:
            try:
                self.zoom.sync(settings)
            except Exception:
                self.stop(now_ns=_now_ns)
                raise

    def stop(self, stale: bool = False, now_ns: int | None = None) -> None:
        cleanup.stop(self, THIRD_PERSON, TRANSITION, BLEND, TELEPORT, stale, now_ns)
