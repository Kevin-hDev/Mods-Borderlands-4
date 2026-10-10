"""Constant-space diagnostics: periodic totals never consume the incident channel."""
from . import collision_config as config


class CollisionDiagnostics:
    def __init__(self, note, status=None):
        self.note = note
        # The 30 s totals go to the SDK log only, below the console's level: printed there they read as an endless
        # error (Kevin, 2026-10-10, « des erreurs de collision qui se répètent »). Incidents keep the note.
        self.status = status
        self.reset()

    def reset(self):
        self.frames = self.errors = 0
        self.max_us = self.total_us = 0.0
        self.last_status = self.last_incident = None
        self.incident = False
        self.sink_failed = False

    def record(self, now, elapsed, error=None, held=False):
        duration = max(0, elapsed) / 1000
        self.total_us += duration
        self.max_us = max(self.max_us, duration)
        if error is not None:
            self.errors += 1
            if (not self.incident and (self.last_incident is None
                    or now - self.last_incident >= config.INCIDENT_PERIOD_NS)):
                self.last_incident = now
                reason = str(error) if str(error) in config.KNOWN_REFUSALS else ''
                self._note(f'{config.HELD_FAILURE if held else config.POSITION_FAILURE}: {type(error).__name__}'
                           + (f' ({reason})' if reason else ''))
            self.incident = True
        else:
            self.frames += 1
            self.incident = False
        if (self.last_status is None and error is None
                or self.last_status is not None and now - self.last_status >= config.STATUS_PERIOD_NS):
            self.last_status = now
            self._note(config.STATUS_LINE.format(
                frames=self.frames, errors=self.errors,
                max_us=self.max_us, mean_us=self.total_us / (self.frames + self.errors)), quiet=True)
        elif self.last_status is None:
            # The first failure already has its own line; keep a later aggregate scheduled.
            self.last_status = now

    def _note(self, message, quiet=False):
        if self.sink_failed:
            return
        try:
            (self.status if quiet and self.status is not None else self.note)(message)
        except Exception:
            # A broken sink is contained; no exception may cross the native callback.
            self.sink_failed = True
