"""The beam's own energy: a number this mod keeps, apart from the game's stamina (Kevin, 2026-10-01).

Firing drains it; left alone for a moment, it comes back. A shot begins at a press, never by itself: a key held
while the beam is off shuts the reserve until it is let go. Without that rule a key held on an emptied reserve would
fire one frame out of every few as the energy trickled back, and a key pressed again on an empty reserve fired two
frames at the first crumb of energy (audit of 2026-10-01).
"""

MAXIMUM = 100.0


class Reserve:
    def __init__(self) -> None:
        self.left = MAXIMUM
        self.idle_s = 0.0
        self.shut = False

    def can_fire(self, cost: float = 0.0) -> bool:
        """Whether the beam may fire. `cost` is what a shot must be able to pay to begin; one already lit goes on to
        the last of the energy."""
        return self.left > 0.0 and self.left >= cost and not self.shut

    def spend(self, seconds: float, per_second: float) -> None:
        """Drains for that long; empties at most."""
        self.idle_s = 0.0
        self.left = max(0.0, self.left - max(0.0, per_second) * max(0.0, seconds))

    def rest(self, seconds: float, per_second: float, delay_s: float, key_held: bool) -> None:
        """The beam is off: counts the time since the last drain and refills once the delay has passed. The key held
        meanwhile shuts the reserve, the key let go opens it."""
        self.shut = key_held
        self.idle_s += max(0.0, seconds)
        if self.idle_s >= delay_s:
            self.left = min(MAXIMUM, self.left + max(0.0, per_second) * max(0.0, seconds))
