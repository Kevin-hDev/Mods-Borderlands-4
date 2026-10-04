"""Bounded, nontechnical ADS diagnostics; no object names or addresses are printed."""
MESSAGES = {
    "unavailable": "third-person aiming unavailable; native aiming retained",
    "unknown_weapon": "weapon category unavailable; native aiming retained",
    "heavy_native": "heavy weapon uses native aiming pending validation",
    "animation_pending": "aiming animation temporarily unavailable; waiting",
    "cleanup_pending": "aiming restoration pending; new presentation blocked",
    "cleanup_failed": "aiming restoration unavailable; camera ownership retained",
    "wrong_thread": "aiming callback refused on another thread; presentation disabled",
    "reference_unavailable": "aiming reference unavailable; native aiming retained",
    "publication_refused": "aiming publication refused; native aiming retained",
    "owner_abandoned": "expired aiming ownership abandoned without writing game objects",
}


class Feedback:
    def __init__(self, log):
        self.log, self.last = log, None
        self.reason = None

    def report(self, context, reason):
        self.reason = reason
        current = (context, reason)
        if current != self.last:
            self.last = current
            self.log(MESSAGES[reason])
