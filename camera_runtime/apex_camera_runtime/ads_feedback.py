"""Bounded, nontechnical ADS diagnostics; no object names or addresses are printed."""
from .generated_ads import (ERROR_GAME_COMPATIBILITY, ERROR_OBJECT_TABLE, ERROR_SDK_COMPATIBILITY,
                            ERROR_SDK_EXPORT, ERROR_SIGNATURE)

NATIVE_FAILURES = {
    ERROR_SDK_COMPATIBILITY: "sdk_compatibility",
    ERROR_GAME_COMPATIBILITY: "game_compatibility",
    ERROR_SIGNATURE: "signature_mismatch",
    ERROR_SDK_EXPORT: "sdk_export_missing",
    ERROR_OBJECT_TABLE: "object_table_unavailable",
}
MESSAGES = {
    "unavailable": "third-person aiming unavailable; native aiming retained",
    "preparation_failed": "third-person aiming could not start; native aiming retained",
    "unknown_weapon": "weapon category unavailable; native aiming retained",
    "heavy_native": "heavy weapon uses native first-person aiming",
    "animation_pending": "aiming animation temporarily unavailable; waiting",
    "cleanup_pending": "aiming restoration pending; new presentation blocked",
    "cleanup_failed": "aiming restoration unavailable; camera ownership retained",
    "wrong_thread": "aiming callback refused on another thread; presentation disabled",
    "reference_unavailable": "aiming reference unavailable; native aiming retained",
    "publication_refused": "aiming publication refused; native aiming retained",
    "owner_abandoned": "expired aiming ownership abandoned without writing game objects",
}
MAX_DIAGNOSTICS = 32
DIAGNOSTIC = "aiming diagnostic stage={stage} error_type={kind}"


def native_failure_kind(status):
    return NATIVE_FAILURES.get(status, "native_failure") if type(status) is int else "invalid_status"


def native_status_code(status):
    return status if type(status) is int and -(1 << 31) <= status < (1 << 31) else "invalid"


def exception_kind(error):
    name = type(error).__name__
    return name if name.isascii() and name.isidentifier() and len(name) <= 80 else "Exception"


class Feedback:
    def __init__(self, log):
        self.log, self.last = log, None
        self.reason = None
        self.terminal = False
        self._diagnostics = {}

    def begin_frame(self):
        # Permanence comes from bridge/thread state, never from an exception's message category.
        if not self.terminal:
            self.reason = None

    def diagnostic(self, stage, kind):
        key = stage, kind
        if key in self._diagnostics:
            return
        if len(self._diagnostics) >= MAX_DIAGNOSTICS:
            self._diagnostics.pop(next(iter(self._diagnostics)))
        self._diagnostics[key] = True
        self.log(DIAGNOSTIC.format(stage=stage, kind=kind))

    def exception(self, context, reason, stage, error):
        self.report(context, reason)
        self.diagnostic(stage, exception_kind(error))

    def report(self, context, reason, *, terminal=False):
        self.reason = reason
        self.terminal = terminal
        current = (context, reason)
        if current != self.last:
            self.last = current
            self.log(MESSAGES[reason])
