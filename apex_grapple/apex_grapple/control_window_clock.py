"""One process-wide owner for every Apex panel and its pause-safe update timer."""

import sys
from types import ModuleType

from .control_timer_native import NativeTimer

STATE = "_apex_shared_menu_clock_v1"


class Clock:
    def __init__(self, native):
        self.native = native
        self.owner = self.cancel = self.callback = None
        self.busy = False
        self.error = None

    def claim(self, owner, cancel):
        self.native.check_thread()
        if self.busy:
            raise RuntimeError("Menu update in progress")
        if self.owner is not None:
            if self.owner == owner:
                raise RuntimeError("Menu cleanup pending")
            self.cancel()
            if self.owner is not None:
                raise RuntimeError("Previous menu cleanup pending")
        self.owner, self.cancel = owner, cancel

    def start(self, owner, callback):
        self.native.check_thread()
        if self.owner != owner:
            raise RuntimeError("Menu ownership changed")
        self.callback = callback
        try:
            self.native.start(self.dispatch)
        except Exception:
            self.callback = None
            raise
        return True

    def stop(self, owner):
        if self.owner == owner:
            self.native.stop()
            self.callback = None

    def release(self, owner):
        if self.owner == owner:
            self.native.check_thread()
            if self.native.timer:
                raise RuntimeError("Menu timer still active")
            self.owner = self.cancel = self.callback = None

    def dispatch(self):
        if self.busy or self.callback is None:
            return
        self.busy = True
        try:
            if self.native.available():
                self.callback(None, None, None, None)
        except BaseException as error:
            self.error = type(error).__name__
            try:
                if self.cancel is not None:
                    self.cancel()
            except BaseException as cleanup_error:
                self.error = type(cleanup_error).__name__
                self.callback = None  # Keep ownership until explicit recovery succeeds.
        finally:
            self.busy = False


def shared():
    state = sys.modules.get(STATE)
    if state is None:
        state = ModuleType(STATE)
        state.clock = Clock(NativeTimer())
        sys.modules[STATE] = state
    return state.clock
