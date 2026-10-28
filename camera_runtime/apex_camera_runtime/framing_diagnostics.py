"""Constant-space framing notices; the sink never governs rendered settings."""
import time

from .diagnostics_config import INCIDENT_PERIOD_NS, MAX_SUPPRESSED
from .framing_status import MESSAGES


class Diagnostics:
    def __init__(self, log, clock=None):
        self.log = log
        self.clock = clock if clock is not None else lambda: time.perf_counter_ns()
        self.last_incident = None
        self.reason = None
        self.pending = False
        self.suppressed = 0
        self.sink_failed = False

    def rearm(self):
        """Retry a failed sink on camera activation without resetting the rate budget."""
        self.sink_failed = False

    def report(self, reason):
        changed = reason != self.reason
        self.reason = reason
        if reason is None:
            self.pending = False
            return
        if reason not in MESSAGES:
            raise ValueError("Unknown framing diagnostic")
        self.pending = self.pending or changed
        if not self.pending or self.sink_failed:
            return
        now = self.clock()
        if self.last_incident is not None and now - self.last_incident < INCIDENT_PERIOD_NS:
            if changed:
                self.suppressed = min(MAX_SUPPRESSED, self.suppressed + 1)
            return
        self.last_incident = now
        try:
            self.log(f"{MESSAGES[reason]} suppressed={self.suppressed}")
        except Exception:
            # A journal outage must not invalidate an otherwise valid context publication.
            self.sink_failed = True
        else:
            self.pending = False
            self.suppressed = 0
