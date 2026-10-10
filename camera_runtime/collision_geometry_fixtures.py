"""Analytic half-planes and vertical cylinders at the SDK physics boundary."""
import math
from types import SimpleNamespace as NS


class Geometry:
    def __init__(self, planes=(), pillars=(), walls=()):
        self.planes, self.pillars, self.walls = planes, pillars, walls
        self.spheres = 0
        self.detailed_only = False

    @staticmethod
    def vector(value):
        return value.X, value.Y, value.Z

    def trace(self, first, last, radius, detailed):
        if self.detailed_only and not detailed:
            return False, NS()
        start, end = self.vector(first), self.vector(last)
        movement = tuple(b - a for a, b in zip(start, end))
        length = math.dist(start, end)
        hits = []
        for normal, offset in self.planes:
            gap = sum(a * n for a, n in zip(start, normal)) - offset
            approach = sum(a * n for a, n in zip(movement, normal))
            if gap < radius:
                hits.append((0, radius - gap))
            elif approach < 0 and gap + approach <= radius:
                hits.append(((radius - gap) / approach, 0))
        for x, y, size in self.pillars:
            hits.extend(self.circle_hits(start, movement, x, y, size + radius))
        for first, last in self.walls:
            hits.extend(self.wall_hits(start, movement, first, last, radius))
        if not hits:
            return False, NS()
        fraction, depth = min(hits)
        return True, NS(Distance=length * fraction, bStartPenetrating=depth > 0,
                        PenetrationDepth=depth)

    @staticmethod
    def circle_hits(start, movement, x, y, radius):
        dx, dy = start[0] - x, start[1] - y
        a = movement[0] ** 2 + movement[1] ** 2
        b = 2 * (dx * movement[0] + dy * movement[1])
        c = dx * dx + dy * dy - radius * radius
        if c < 0:
            return [(0, radius - math.hypot(dx, dy))]
        if a > 0 and b * b - 4 * a * c >= 0:
            fraction = (-b - math.sqrt(b * b - 4 * a * c)) / (2 * a)
            if 0 <= fraction <= 1:
                return [(fraction, 0)]
        return []

    @classmethod
    def wall_hits(cls, start, movement, first, last, radius):
        length = math.dist(first, last)
        tangent = tuple((b - a) / length for a, b in zip(first, last))
        normal = (-tangent[1], tangent[0])
        relative = (start[0] - first[0], start[1] - first[1])
        along = sum(a * b for a, b in zip(relative, tangent))
        gap = sum(a * b for a, b in zip(relative, normal))
        closest = math.hypot(gap, along - min(length, max(0, along)))
        if closest < radius:
            return [(0, radius - closest)]
        approach = sum(a * b for a, b in zip(movement, normal))
        forward = sum(a * b for a, b in zip(movement, tangent))
        hits = []
        if approach:
            for side in (-radius, radius):
                fraction = (side - gap) / approach
                if 0 <= fraction <= 1 and 0 <= along + fraction * forward <= length:
                    hits.append((fraction, 0))
        for x, y in (first, last):
            hits.extend(cls.circle_hits(start, movement, x, y, radius))
        return hits

    def SphereTraceSingle(self, actor, first, last, radius, channel, detailed, *args):
        self.spheres += 1
        return self.trace(first, last, radius, detailed)
