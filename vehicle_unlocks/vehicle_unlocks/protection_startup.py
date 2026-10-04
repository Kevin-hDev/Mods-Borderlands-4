"""Wait for cold DLC loading, then remove observation; never distribute rewards."""
from . import protection_config as cfg


class Waiter:
    def __init__(self, controller, clock, install, remove):
        self.controller, self.clock = controller, clock
        self.install, self.remove = install, remove
        self.active = False
        self.deadline = self.next_poll = self.attempts = 0

    def sync(self):
        if self.controller.pending and not self.active:
            self.deadline = self.clock() + cfg.STARTUP_TIMEOUT_NS
            self.next_poll = self.attempts = 0
            try:
                self.install(self.tick)
                self.active = True
            except Exception:
                self.controller.fail(RuntimeError('Startup hook unavailable'))
        elif not self.controller.pending and self.active:
            self.active = False
            try:
                self.remove()
            except Exception:
                # A remaining callback is inert, and no further writes are allowed.
                self.controller.fail(RuntimeError('Startup hook unavailable'))

    def tick(self, *_):
        if not self.active:
            return
        now = self.clock()
        if not self.controller.pending:
            self.sync()
            return
        if now >= self.deadline or self.attempts >= cfg.STARTUP_MAX_ATTEMPTS:
            self.controller.fail(RuntimeError('DLC catalogue startup timeout'))
        elif now >= self.next_poll:
            self.next_poll = now + cfg.STARTUP_POLL_NS
            self.attempts += 1
            self.controller.resume()
        self.sync()
