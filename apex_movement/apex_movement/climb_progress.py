"""Measures distance travelled during a wall climb and detects a character blocked in place."""

import math
from typing import Any

# A moving climb covers at least 20 units in 0.2 s at the slowest allowed speed. Ten leaves room for collisions and
# slopes while still stopping a character held under an obstacle.
STALL_NS = 200_000_000
MIN_PROGRESS = 10.0


def _point(moment: Any) -> tuple[float, float, float]:
    return float(moment.x), float(moment.y), float(moment.z)


class Tracker:
    def __init__(self) -> None:
        self.distance = 0.0
        self._last = (0.0, 0.0, 0.0)
        self._checkpoint = 0.0
        self._checkpoint_ns = 0

    def reset(self, moment: Any) -> None:
        self.distance = self._checkpoint = 0.0
        self._last = _point(moment)
        self._checkpoint_ns = int(moment.now_ns)

    def update(self, moment: Any) -> bool:
        """Adds the latest three-dimensional movement and says whether progress has stalled."""
        current = _point(moment)
        self.distance += math.dist(self._last, current)
        self._last = current
        if self.distance >= self._checkpoint + MIN_PROGRESS:
            self._checkpoint = self.distance
            self._checkpoint_ns = int(moment.now_ns)
            return False
        return int(moment.now_ns) - self._checkpoint_ns >= STALL_NS
