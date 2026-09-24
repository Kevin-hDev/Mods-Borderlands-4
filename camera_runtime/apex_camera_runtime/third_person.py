"""Own the native shift, camera mode and transition hooks as one retryable unit."""

import time
from typing import Any, Callable

from . import aiming, cleanup
from .lifetime import CameraLifetime
from .transitions import THIRD_PERSON, VEHICLE_MODE, TransitionHooks

TRANSITION = "Default"
BLEND = -1.0
TELEPORT = False
CLEANUP_PATH = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
MAX_CLEANUP_ATTEMPTS = 3
CLEANUP_RETRY_FIRST_NS = 100_000_000


class ThirdPersonController:
    def __init__(self, hooks: Any, bridge: Any, identifier: str,
                 weak_ref: Callable | None = None, log: Callable | None = None,
                 collision: Any = None, clock: Callable[[], int] | None = None) -> None:
        self.hooks = hooks
        self.bridge = bridge
        self.identifier = identifier
        self.weak_ref = weak_ref or (lambda item: lambda: item)
        self.log = log or (lambda _message: None)
        self.collision = collision
        self.clock = clock or time.perf_counter_ns
        self._lifetime = CameraLifetime(self.weak_ref)
        self._transitions = None
        self._bridge_started = self._hooks_installed = False
        self._mode_pushes = 0
        self._cleanup_hook = False
        self._cleanup_attempts = 0
        self._next_cleanup_ns = 0
        self._cleanup_stale = False
        self._disable_cleanup_attempted = False
        self._pending_identity = None
        self._recovery_requested = False
        self._in_vehicle = False
        self._aiming = False
        self._aim_returning = False
        self._suspensions: set[str] = set()

    @property
    def cleanup_pending(self) -> bool:
        return self._bridge_started or self._hooks_installed or self._mode_pushes > 0

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

    def _on_transition(self, requested: str, effective: str) -> None:
        if requested == VEHICLE_MODE:
            self._suspend("vehicle", True)
            try:
                aiming.prepare_vehicle(self, THIRD_PERSON, TRANSITION, BLEND, TELEPORT)
            except Exception:
                self._suspend("vehicle", False)
                raise
            self._in_vehicle = True
        elif effective == THIRD_PERSON:
            self._in_vehicle = False

    def _start(self, pc: Any) -> None:
        actor = getattr(pc, "OakCharacter", None)
        manager = getattr(pc, "PlayerCameraManager", None)
        if actor is None or manager is None:
            return
        self._lifetime.bind(pc, actor, manager)
        self._recovery_requested = False
        try:
            self.bridge.start(manager)
            self._bridge_started = True
            self._transitions = TransitionHooks(
                self.hooks, self.identifier, pc, self.log, self._on_transition)
            self._transitions.install()
            self._hooks_installed = True
            manager.PushActorCameraMode(actor, THIRD_PERSON, TRANSITION, BLEND, TELEPORT)
            self._mode_pushes += 1
        except Exception as setup_error:
            try:
                self.stop()
            except Exception as cleanup_error:
                raise RuntimeError("third person setup cleanup incomplete") from cleanup_error
            raise setup_error

    def sync(self, _owner: str, pc: Any, settings: Any, _now_ns: int) -> None:
        enabled = settings.third_person_enabled()
        if not enabled or pc is None:
            if self.cleanup_pending and self._cleanup_attempts >= MAX_CLEANUP_ATTEMPTS:
                if enabled or self._disable_cleanup_attempted:
                    return
                self._disable_cleanup_attempted = True
                try:
                    self.stop(stale=self._cleanup_stale, now_ns=_now_ns)
                except RuntimeError:
                    self.log("manual third person cleanup failed after bounded retries")
            elif self._cleanup_hook:
                self._retry_cleanup(_now_ns)
            else:
                self.stop(now_ns=_now_ns)
            return
        current, actor, _manager, target, changed = self._lifetime.inspect(pc)
        if actor is None and self._in_vehicle and current is not None and target[0] == self._lifetime.ids[0]:
            return
        if changed:
            if target != self._pending_identity:
                self._pending_identity = target
                self._cleanup_attempts = self._next_cleanup_ns = 0
                self._disable_cleanup_attempted = False
                self._remove_cleanup_hook()
            if self.cleanup_pending:
                if self._cleanup_attempts >= MAX_CLEANUP_ATTEMPTS:
                    return
                if self._cleanup_hook:
                    self._retry_cleanup(_now_ns)
                else:
                    self.stop(stale=True, now_ns=_now_ns)
                if self.cleanup_pending:
                    return
            self._pending_identity = None
            self._start(pc)
        elif self.cleanup_pending and self._cleanup_attempts >= MAX_CLEANUP_ATTEMPTS:
            return
        elif (self.cleanup_pending
              and not (self._bridge_started and self._hooks_installed
                       and (self._mode_pushes > 0 or self._aiming or self._in_vehicle))):
            # A re-enable after partial cleanup must rebuild one complete owned unit.
            if self._cleanup_hook:
                self._retry_cleanup(_now_ns)
            else:
                self.stop(now_ns=_now_ns)
            if self.cleanup_pending:
                return
            self._start(pc)
        if not self.cleanup_pending:
            return
        actor, manager = self._lifetime.owned()
        if actor is None or manager is None:
            if self._cleanup_hook:
                self._retry_cleanup(_now_ns)
            else:
                self.stop(stale=True, now_ns=_now_ns)
            return
        mode = str(manager.GetActorCameraMode(actor))
        if mode == VEHICLE_MODE:
            if not self._in_vehicle:
                self._suspend("vehicle", True)
                aiming.prepare_observed_vehicle(self)
            self._in_vehicle = True
            self._recovery_requested = False
            self._suspend("vehicle", True)
        elif self._in_vehicle and mode == THIRD_PERSON:
            self._in_vehicle = False
            if not self._mode_pushes:
                return
        elif aiming.sync(self, pc, actor, manager, mode, THIRD_PERSON, TRANSITION):
            return
        elif mode == THIRD_PERSON:
            self._in_vehicle = False
            self._recovery_requested = False
            self._suspend("vehicle", False)
        elif (mode in ("Default", "Slide") and not self._in_vehicle
              and not self._recovery_requested):
            manager.PushActorCameraMode(actor, THIRD_PERSON, TRANSITION, BLEND, TELEPORT)
            self._mode_pushes += 1
            self._recovery_requested = True
        if self.collision is not None and "vehicle" not in self._suspensions:
            self.collision.sample(_now_ns, actor, self.bridge,
                                  lambda blocked: self._suspend("collision", blocked))

    def _remove_cleanup_hook(self) -> None:
        identifier = f"{self.identifier}:cleanup"
        if self._cleanup_hook and self.hooks.has_hook(CLEANUP_PATH, self.hooks.Type.POST, identifier):
            self.hooks.remove_hook(CLEANUP_PATH, self.hooks.Type.POST, identifier)
        self._cleanup_hook = False

    def _schedule_cleanup(self, now_ns: int, stale: bool) -> None:
        self._cleanup_stale = self._cleanup_stale or stale
        if self._cleanup_hook or self._cleanup_attempts >= MAX_CLEANUP_ATTEMPTS:
            return
        identifier = f"{self.identifier}:cleanup"

        def retry(_obj, _args, _ret, _func):
            self._retry_cleanup(self.clock())
            return None

        self.hooks.add_hook(CLEANUP_PATH, self.hooks.Type.POST, identifier, retry)
        self._cleanup_hook = True
        self._next_cleanup_ns = now_ns + CLEANUP_RETRY_FIRST_NS

    def _retry_cleanup(self, now_ns: int) -> None:
        if not self.cleanup_pending or now_ns < self._next_cleanup_ns:
            return
        if self._cleanup_attempts >= MAX_CLEANUP_ATTEMPTS:
            self._remove_cleanup_hook()
            return
        self._cleanup_attempts += 1
        try:
            self.stop(stale=self._cleanup_stale, now_ns=now_ns)
        except RuntimeError:
            if self._cleanup_attempts >= MAX_CLEANUP_ATTEMPTS:
                self._remove_cleanup_hook()
                self.log("third person cleanup stopped after bounded retries")
            else:
                wait = CLEANUP_RETRY_FIRST_NS * (2 ** self._cleanup_attempts)
                self._next_cleanup_ns = now_ns + wait

    def stop(self, stale: bool = False, now_ns: int | None = None) -> None:
        cleanup.stop(self, THIRD_PERSON, TRANSITION, BLEND, TELEPORT, stale, now_ns)
