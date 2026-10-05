"""Keep the upper body visible by limiting only the fresh added camera offset."""
import math
from . import collision_config as config
from .collision_path import point


class Visibility:
    def __init__(self, kismet, sdk):
        self.kismet, self.sdk = kismet, sdk
        self.cache = {}

    def begin_frame(self):
        # Geometry can move every frame; never retain a sightline across callbacks.
        self.cache.clear()

    def distance(self, actor, anchor, desired, available, target=None):
        target = self.target(actor) if target is None else target
        length = math.dist(anchor, desired)
        fraction = available / length
        def candidate(value):
            return tuple(a + (b - a) * value for a, b in zip(anchor, desired))
        if self.clear(actor, candidate(fraction), target):
            return available
        if not self.clear(actor, anchor, target):
            return 0.0  # No verified view beyond the current native position.
        low, high = 0.0, fraction
        for _ in range(config.VISIBILITY_STEPS):
            middle = (low + high) / 2
            if self.clear(actor, candidate(middle), target):
                low = middle
            else:
                high = middle
        return low * length

    def recovery_distance(self, actor, anchor, desired, available, previous, target):
        length = math.dist(anchor, desired)
        fraction = available / length
        def candidate(value):
            return tuple(a + (b - a) * value for a, b in zip(anchor, desired))
        if fraction <= previous:
            return available
        # Sample the whole return path, not the time-step-sized movement. Endpoints
        # alone miss a thin post's shadow when both sides of it are visible.
        steps = min(config.VISIBILITY_PATH_STEPS, max(1, math.ceil(
            (fraction - previous) * length / config.VISIBILITY_SAMPLE_SPACING)))
        low = previous
        for index in range(1, steps + 1):
            high = previous + (fraction - previous) * index / steps
            if not self.clear(actor, candidate(high), target):
                for _ in range(config.VISIBILITY_STEPS):
                    middle = (low + high) / 2
                    if self.clear(actor, candidate(middle), target):
                        low = middle
                    else:
                        high = middle
                return low * length
            low = high
        return available

    @staticmethod
    def target(actor):
        origin = actor.K2_GetActorLocation()
        half = float(actor.CapsuleComponent.GetScaledCapsuleHalfHeight())
        if not math.isfinite(half) or not 0 < half <= config.MAX_LENGTH:
            raise ValueError("invalid camera visibility target")
        return point((origin.X, origin.Y, origin.Z + half * config.UPPER_BODY_FRACTION))

    def clear(self, actor, position, target):
        key = (position, target)
        if key in self.cache:
            return self.cache[key]
        result = self._clear(actor, position, target)
        # Bound cached sightlines; eviction recomputes geometry instead of assuming it clear.
        if len(self.cache) >= config.VISIBILITY_CACHE_SIZE:
            self.cache.clear()
        self.cache[key] = result
        return result

    def _clear(self, actor, position, target):
        first = self.sdk.make_struct("Vector", X=position[0], Y=position[1], Z=position[2])
        last = self.sdk.make_struct("Vector", X=target[0], Y=target[1], Z=target[2])
        for complex_trace in (False, True):
            answer = self.kismet.LineTraceSingle(
                actor, first, last, config.TRACE_CHANNEL, complex_trace, [actor], 0,
                self.sdk.make_struct("HitResult"), True, self.sdk.make_struct("LinearColor"),
                self.sdk.make_struct("LinearColor"), 0.0)
            if not isinstance(answer, tuple) or not 2 <= len(answer) <= 3 or type(answer[0]) is not bool:
                raise ValueError("invalid camera visibility result")
            if answer[0]:
                return False
        return True
