"""Constant-space diagnostics: periodic totals never consume the incident channel."""
from . import collision_config as config


class CollisionDiagnostics:
    def __init__(self, note):
        self.note = note
        self.reset()

    def reset(self):
        self.frames = self.blocked = self.errors = 0
        self.max_us = self.total_us = 0.0
        self.last_status = self.last_incident = None
        self.incident = False
        self.sink_failed = False

    def record(self, now, elapsed, blocked=False, error=None):
        duration = max(0, elapsed) / 1000
        self.total_us += duration
        self.max_us = max(self.max_us, duration)
        if error is not None:
            self.errors += 1
            if (not self.incident and (self.last_incident is None
                    or now - self.last_incident >= config.INCIDENT_PERIOD_NS)):
                self.last_incident = now
                self._note(f'{config.POSITION_FAILURE}: {type(error).__name__}')
            self.incident = True
        else:
            self.frames += 1
            self.blocked += int(blocked)
            self.incident = False
        if (self.last_status is None and error is None
                or self.last_status is not None and now - self.last_status >= config.STATUS_PERIOD_NS):
            self.last_status = now
            self._note(config.STATUS_LINE.format(
                frames=self.frames, blocked=self.blocked, errors=self.errors,
                max_us=self.max_us, mean_us=self.total_us / (self.frames + self.errors)))
        elif self.last_status is None:
            # The first failure already has its own line; keep a later aggregate scheduled.
            self.last_status = now
    def _note(self, message):
        if self.sink_failed:
            return
        try:
            self.note(message)
        except Exception:
            # A broken sink is contained; no exception may cross the native callback.
            self.sink_failed = True
