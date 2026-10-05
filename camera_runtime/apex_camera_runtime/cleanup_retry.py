"""Own the single bounded hook used to retry incomplete camera cleanup."""

from typing import Any, Callable

CLEANUP_PATH = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
MAX_CLEANUP_ATTEMPTS = 3
CLEANUP_RETRY_FIRST_NS = 100_000_000


class CleanupRetry:
    def __init__(self, hooks: Any, identifier: str, clock: Callable[[], int],
                 log: Callable[[str], None], label: str = 'third person') -> None:
        self.hooks = hooks
        self.identifier = identifier
        self.clock = clock
        self.log = log
        self.label = label
        self.pending = False
        self.waiting = False
        self.attempts = 0
        self.next_ns = 0
        self.stale = False
        self.disable_attempted = False

    @property
    def exhausted(self) -> bool:
        return self.attempts >= MAX_CLEANUP_ATTEMPTS

    def cancel(self) -> None:
        hook_id = f"{self.identifier}:cleanup"
        if self.pending and self.hooks.has_hook(CLEANUP_PATH, self.hooks.Type.POST, hook_id):
            self.hooks.remove_hook(CLEANUP_PATH, self.hooks.Type.POST, hook_id)
        self.pending = False
        self.waiting = False

    def reset(self) -> None:
        self.cancel()
        self.attempts = 0
        self.next_ns = 0
        self.stale = False
        self.disable_attempted = False

    def schedule(self, controller: object, now_ns: int, stale: bool) -> None:
        self.stale = self.stale or stale
        if self.pending or self.exhausted:
            return
        hook_id = f"{self.identifier}:cleanup"

        def retry(_obj, _args, _ret, _func):
            self.retry(controller, self.clock())
            return None

        self.hooks.add_hook(CLEANUP_PATH, self.hooks.Type.POST, hook_id, retry)
        self.pending = True
        self.next_ns = now_ns + CLEANUP_RETRY_FIRST_NS

    def schedule_wait(self, controller: object, now_ns: int, stale: bool) -> None:
        # The same observer survives mod disable; natural HUD restoration is not a failed cleanup.
        self.waiting = True
        self.schedule(controller, now_ns, stale)

    def retry(self, controller: object, now_ns: int) -> None:
        if not getattr(controller, "cleanup_pending", False) or now_ns < self.next_ns:
            return
        if self.waiting:
            if not controller.ads.stop():
                self.next_ns = now_ns + CLEANUP_RETRY_FIRST_NS
                return
            self.waiting = False
        if self.exhausted:
            self.cancel()
            return
        self.attempts += 1
        try:
            controller.stop(stale=self.stale, now_ns=now_ns)
        except RuntimeError:
            if self.exhausted:
                self.cancel()
                self.log(f"{self.label} cleanup stopped after bounded retries")
            else:
                self.next_ns = now_ns + CLEANUP_RETRY_FIRST_NS * (2 ** self.attempts)
            return
        if not getattr(controller, "cleanup_pending", False):
            self.reset()
