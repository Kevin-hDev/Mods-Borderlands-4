"""Analytic geometry with alternative engine reports for a touching departure volume."""
import math
from types import SimpleNamespace as NS

from collision_geometry_fixtures import Geometry


class ContactGeometry(Geometry):
    def __init__(self, planes=(), pillars=(), depth=0.0, penetrating=True, band=1e-8):
        super().__init__(planes=planes, pillars=pillars)
        self.contact_depth = depth
        self.contact_penetrating = penetrating
        self.contact_band = band

    def SphereTraceSingle(self, actor, first, last, radius, channel, detailed, *args):
        answer = super().SphereTraceSingle(actor, first, last, radius, channel, detailed, *args)
        if self.detailed_only and not detailed:
            return answer
        start = self.vector(first)
        gaps = [sum(a * n for a, n in zip(start, normal)) - offset
                for normal, offset in self.planes]
        gaps.extend(math.hypot(start[0] - x, start[1] - y) - size
                    for x, y, size in self.pillars)
        if gaps and abs(radius - min(gaps)) <= self.contact_band:
            return True, NS(Distance=0.0, bStartPenetrating=self.contact_penetrating,
                            PenetrationDepth=self.contact_depth)
        return answer


class UnknownOverlapGeometry(Geometry):
    """Engine overlap reports can omit the separation depth at a stationary endpoint."""
    def SphereTraceSingle(self, actor, first, last, radius, channel, detailed, *args):
        answer = super().SphereTraceSingle(actor, first, last, radius, channel, detailed, *args)
        if answer[0] and self.vector(first) == self.vector(last):
            answer[-1].PenetrationDepth = 0.0
        return answer


class MovingOnlyGeometry(Geometry):
    """Model an SDK boundary that supplies no overlap result for a zero-length sweep."""
    def SphereTraceSingle(self, actor, first, last, radius, channel, detailed, *args):
        if self.vector(first) == self.vector(last):
            self.spheres += 1
            return False, NS()
        return super().SphereTraceSingle(actor, first, last, radius, channel, detailed, *args)
