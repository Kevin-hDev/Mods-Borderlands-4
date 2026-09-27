"""Advance one ordered settings transaction, including asynchronous camera choices."""

import time

# A camera startup normally needs one frame; two seconds bounds a failed setup without racing a slow frame.
TRANSACTION_TIMEOUT_NS = 2_000_000_000


def _priority(change):
    option, target = change
    if option.identifier == "third_person":
        return 0 if target is True else 4
    if option.identifier == "orbit":
        return 1 if target is False else 3
    return 2


class Transaction:
    def __init__(self, mod, report, clock=time.perf_counter_ns):
        self.mod = mod
        self.report = report
        self.clock = clock
        self.changes = ()
        self.previous = ()
        self.kind = ""
        self.index = 0
        self.waiting = False
        self.waiting_since = 0
        self.rolling_back = False

    @property
    def pending(self):
        return bool(self.kind)

    @staticmethod
    def _ordered(changes):
        return tuple(sorted(changes, key=_priority))

    def start(self, changes, previous, kind):
        if self.pending:
            return None
        self.changes = self._ordered(changes)
        self.previous = tuple(previous)
        self.kind = kind
        self.index = 0
        self.waiting = False
        self.waiting_since = 0
        self.rolling_back = False
        return self._run()

    def advance(self):
        if not self.pending:
            return None
        return self._run()

    def cancel(self):
        if not self.pending:
            return None
        if self.rolling_back:
            return self._run()
        if self.waiting:
            option, _target = self.changes[self.index]
            status = getattr(option, "camera_status", "refused")
            if status in ("pending", "waiting") and not self._cancel_current(option):
                return None
        return self._fail()

    def _run(self):
        if self.waiting:
            option, target = self.changes[self.index]
            if option.value == target:
                self.waiting = False
                self.waiting_since = 0
                self.index += 1
            elif getattr(option, "camera_status", "refused") in ("pending", "waiting"):
                status = option.camera_status
                if not self._pause():
                    return self._fail() if self._cancel_current(option) else None
                if status == "pending":
                    return None
                self.waiting = False
            else:
                return self._fail()
        while self.index < len(self.changes):
            option, target = self.changes[self.index]
            if option.value == target:
                self.index += 1
                continue
            try:
                option.value = target
            except Exception:
                return self._fail()
            if hasattr(option, "camera_status") and option.value != target:
                if option.camera_status in ("pending", "waiting"):
                    if not self._pause():
                        return self._fail() if self._cancel_current(option) else None
                    return None
                return self._fail()
            self.index += 1
        try:
            self.mod.save_settings()
        except Exception:
            return self._fail()
        return self._finish(not self.rolling_back)

    def _pause(self):
        now = self.clock()
        if not self.waiting_since:
            self.waiting_since = now
        elif now - self.waiting_since > TRANSACTION_TIMEOUT_NS:
            return False
        self.waiting = True
        return True

    @staticmethod
    def _cancel_current(option):
        cancel = getattr(option, "cancel_pending", None)
        return bool(callable(cancel) and cancel())

    def _fail(self):
        if self.rolling_back:
            self.report("panel:save", "Settings could not be restored. Please retry.")
            return self._finish(False)
        self.changes = self._ordered(self.previous)
        self.index = 0
        self.waiting = False
        self.waiting_since = 0
        self.rolling_back = True
        return self._run()

    def _finish(self, success):
        outcome = self.kind, self.previous, success
        self.changes = ()
        self.previous = ()
        self.kind = ""
        self.index = 0
        self.waiting = False
        self.waiting_since = 0
        self.rolling_back = False
        return outcome
