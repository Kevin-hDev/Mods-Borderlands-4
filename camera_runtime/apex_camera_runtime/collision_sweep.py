"""SDK physics boundary: sweep volume against simple and detailed camera geometry."""
import math
from .collision_config import (CONTACT_TOLERANCE, MARGIN, MIN_RADIUS, RADIUS, TRACE_CHANNEL,
                               VOLUME_RECHECKS)
from .collision_path import segment


class SphereSweep:
    def __init__(self, kismet, sdk):
        self.kismet, self.sdk = kismet, sdk
        # The contact behind the last distance, None when clear: the automatic shoulder names it in the log.
        self.hit = None

    def distance(self, actor, anchor, desired):
        self.hit = None
        start, end, length = segment(anchor, desired)
        first = self.sdk.make_struct("Vector", X=start[0], Y=start[1], Z=start[2])
        last = self.sdk.make_struct("Vector", X=end[0], Y=end[1], Z=end[2])
        distance = length
        for complex_trace in (False, True):
            answer = self._trace(actor, first, last, complex_trace)
            if not answer[0]:
                continue
            hit = answer[-1]
            measured = float(hit.Distance)
            if not math.isfinite(measured) or not 0 <= measured <= length:
                raise ValueError("invalid collision contact")
            # Include margin in the volume: a pathwise retreat loses clearance on diagonal steps.
            if measured <= distance:
                distance, self.hit = measured, hit
        return distance

    def _sphere(self, actor, first, last, radius, complex_trace):
        answer = self.kismet.SphereTraceSingle(
            actor, first, last, radius, TRACE_CHANNEL, complex_trace, [actor], 0,
            self.sdk.make_struct("HitResult"), True, self.sdk.make_struct("LinearColor"),
            self.sdk.make_struct("LinearColor"), 0.0)
        if not isinstance(answer, tuple) or not 2 <= len(answer) <= 3 or type(answer[0]) is not bool:
            raise ValueError("invalid collision result")
        return answer

    def _trace(self, actor, first, last, complex_trace):
        radius = RADIUS + MARGIN
        length = math.dist((first.X, first.Y, first.Z), (last.X, last.Y, last.Z))
        for attempt in range(VOLUME_RECHECKS + 1):
            answer = self._sphere(actor, first, last, radius, complex_trace)
            if not answer[0]:
                return answer
            hit = answer[-1]
            measured = float(hit.Distance)
            if not math.isfinite(measured) or not 0 <= measured <= length:
                raise ValueError("invalid collision contact")
            penetrating = bool(getattr(hit, "bStartPenetrating", False))
            if not penetrating and measured > 0.0:
                if measured <= CONTACT_TOLERANCE * VOLUME_RECHECKS:
                    return True, self.sdk.make_struct("HitResult", Distance=0.0)
                return answer
            # The game owns the starting position, which may have less than our preferred margin.
            # Recheck the entire added segment with its measured available volume, including later obstacles.
            # Separation depth belongs only to an initial overlap, never a later hit or stale field.
            depth = float(getattr(hit, "PenetrationDepth", float("nan"))) if penetrating else 0.0
            if not math.isfinite(depth) or not 0 <= depth <= radius:
                raise ValueError("invalid initial collision depth")
            if attempt == VOLUME_RECHECKS:
                return True, self.sdk.make_struct("HitResult", Distance=0.0)
            # Preserve the native camera's measured clearance along the whole segment.
            # A touching departure is not a free segment: use the bounded contact budget and recheck the whole path.
            reduced = radius - depth - CONTACT_TOLERANCE
            if reduced < MIN_RADIUS:
                return True, self.sdk.make_struct("HitResult", Distance=0.0)
            radius = reduced
        return True, self.sdk.make_struct("HitResult", Distance=0.0)
