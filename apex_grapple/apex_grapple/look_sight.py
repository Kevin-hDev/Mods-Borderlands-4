"""Whether any part of a rope shows on screen: numbers in, a yes or a no out, no game here (as look_timing.py).

At the end of a pull seen through the eyes, the arm leaves the screen with the pistol and the rope goes with it, as in
Apex; but if any part of the rope would still cross the screen once the arm is out, the hook comes back into the
muzzle instead, so that no rope ever vanishes before the player's eyes (docs/apex_grapple/pistolet-grappin/
decisions.md, 3 October, "la corde revient dans le pistolet quand elle resterait visible"). The whole rope is tested,
not its ends alone: a rope whose two ends are off screen can still run across it.

The view is the camera's place, its three axes (ahead, left, up, each of length 1) and the tangents of its half
angles across and up. Each piece of the rope is cut down to the part inside the view's four sides; a piece with
anything left shows. The four sides meet at the camera, so nothing behind it is ever inside them.
"""


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _seen(eye, axes, point):
    """`point` as (ahead, left, up) from the camera."""
    offset = tuple(p - e for p, e in zip(point, eye))
    return tuple(_dot(offset, axis) for axis in axes)


def _shows(start, end, half_across: float, half_up: float) -> bool:
    """Whether the straight piece from `start` to `end`, both seen from the camera, has a part inside the view."""
    low, high = 0.0, 1.0
    # Each side as a sum that is not below nothing inside the view: right, left, down and up.
    sides = (lambda p: half_across * p[0] + p[1], lambda p: half_across * p[0] - p[1],
             lambda p: half_up * p[0] + p[2], lambda p: half_up * p[0] - p[2])
    for side in sides:
        a, b = side(start), side(end)
        if a < 0.0 and b < 0.0:
            return False
        if a < 0.0 or b < 0.0:
            cut = a / (a - b)
            if a < 0.0:
                low = max(low, cut)
            else:
                high = min(high, cut)
            if low > high:
                return False
    return True


def shows(eye, axes, half_across: float, half_up: float, points) -> bool:
    """Whether the rope through `points` shows anywhere in the view."""
    seen = [_seen(eye, axes, point) for point in points]
    return any(_shows(a, b, half_across, half_up) for a, b in zip(seen, seen[1:]))
