"""Suspend the shoulder offset while its final-view path crosses geometry."""

import math
from typing import Any, Callable

SAMPLE_NS = 50_000_000


class CollisionGuard:
    def __init__(self, kismet: Any, sdk: Any, note: Callable[[str], None], clear_samples: int = 3) -> None:
        if not isinstance(clear_samples, int) or not 1 <= clear_samples <= 10:
            raise ValueError("invalid collision clear count")
        self.kismet = kismet
        self.sdk = sdk
        self.note = note
        self.clear_samples = clear_samples
        self.next_ns = 0
        self.clear_count = 0
        self.blocked = False
        self.error_reported = False

    def reset(self) -> None:
        self.next_ns = 0
        self.clear_count = 0
        self.blocked = False
        self.error_reported = False

    def _set(self, blocked: bool, update: Callable[[bool], None]) -> None:
        if self.blocked != blocked:
            update(blocked)
            self.blocked = blocked

    def sample(self, now_ns: int, world: Any, bridge: Any, update: Callable[[bool], None]) -> None:
        if now_ns < self.next_ns:
            return
        self.next_ns = now_ns + SAMPLE_NS
        try:
            stats = bridge.stats()
            values = tuple(float(value) for value in (*stats.before, *stats.after))
            if len(values) != 6 or not all(math.isfinite(value) for value in values):
                raise ValueError("invalid camera coordinates")
            start = self.sdk.make_struct("Vector", X=values[0], Y=values[1], Z=values[2])
            end = self.sdk.make_struct("Vector", X=values[3], Y=values[4], Z=values[5])
            hit = bool(self.kismet.LineTraceSingle(
                world, start, end, 1, False, [], 0, self.sdk.make_struct("HitResult"), True,
                self.sdk.make_struct("LinearColor"), self.sdk.make_struct("LinearColor"), 0.0,
            )[0])
        except Exception:
            self.clear_count = 0
            self._set(True, update)
            if not self.error_reported:
                self.note("camera collision check failed; shoulder offset suspended")
                self.error_reported = True
            return
        self.error_reported = False
        if hit:
            self.clear_count = 0
            self._set(True, update)
            return
        if not self.blocked:
            return
        self.clear_count += 1
        if self.clear_count >= self.clear_samples:
            self.clear_count = 0
            self._set(False, update)
