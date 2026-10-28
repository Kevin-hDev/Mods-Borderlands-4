"""Where a thrown object goes once it leaves the hunter's hand (thrown_send.py). Unreal's axes, centimetres.

The measures come from the console trial of 2026-10-21 (docs/investigations/third_person_fov/camera/
2026-10-21-rayon-ohm-et-couteau.md).
"""

import math

# Nothing under the crosshair along its sight line (sky): the point this far along it, as in the trial.
NOTHING_CM = 3000.0
# Closer than this, a point gives no direction worth throwing along.
MIN_FLIGHT_CM = 50.0
# The game spawns a throw 116 to 227 cm from the left hand (eight throws, knife and grenades); a hand farther than
# this from the object is not the one throwing it.
MAX_HAND_CM = 400.0
# The game starts a throw from the view: 1.5 to 1.8 m ahead of the camera, 26 cm off its line, with or without the aim
# alignment. An object born farther off that line, or deeper, came from somewhere else: a grenade's payloads are born
# where it bursts and are thrown by no one.
MAX_LINE_CM = 100.0
MAX_DEPTH_CM = 600.0
# The hand is about 2 m from the game's spawn: a larger turn means a point so close that the throw would leave the hand
# sideways, worse to see than the game's own.
MAX_TURN_DEG = 60.0


def _length(vector) -> float:
    return math.sqrt(sum(part * part for part in vector))


def _dot(first, second) -> float:
    return sum(a * b for a, b in zip(first, second))


def _cross(a, b) -> tuple:
    return a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]


def _towards(origin, point) -> tuple | None:
    offset = [p - o for p, o in zip(point, origin)]
    length = _length(offset)
    return None if length < MIN_FLIGHT_CM else tuple(part / length for part in offset)


def target(camera, forward, distance_cm) -> tuple:
    """The point under the crosshair: along the camera's forward, at what its line meets or NOTHING_CM."""
    reach = NOTHING_CM if distance_cm is None else distance_cm
    return tuple(c + f * reach for c, f in zip(camera, forward))


def from_line(point, camera, forward) -> tuple:
    """(depth along the camera's forward, distance off its line) of a point."""
    offset = [p - c for p, c in zip(point, camera)]
    depth = _dot(offset, forward)
    return depth, math.sqrt(max(0.0, _dot(offset, offset) - depth * depth))


def born_as_throw(point, camera, forward, hand) -> bool:
    depth, off = from_line(point, camera, forward)
    return 0.0 <= depth <= MAX_DEPTH_CM and off <= MAX_LINE_CM and math.dist(point, hand) <= MAX_HAND_CM


def turned(velocity, start, hand, aim) -> tuple | None:
    """The game's launch from start, turned so that it leaves the hand for the aimed point: same speed, and a grenade
    keeps the arc the game gave it. None when a point is too close or the turn too large."""
    first, second = _towards(start, aim), _towards(hand, aim)
    if first is None or second is None or not _length(velocity) > 0.0:
        return None
    cos = max(-1.0, min(1.0, _dot(first, second)))
    if cos < math.cos(math.radians(MAX_TURN_DEG)):
        return None
    axis = _cross(first, second)
    sin = _length(axis)
    if sin < 1e-9:
        return tuple(velocity)
    axis = tuple(part / sin for part in axis)
    # Rodrigues' rotation of the launch about the axis that takes the game's line onto the hand's.
    across, along = _cross(axis, velocity), _dot(axis, velocity) * (1.0 - cos)
    return tuple(v * cos + c * sin + k * along for v, c, k in zip(velocity, across, axis))


def angle_deg(first, second) -> float:
    lengths = _length(first) * _length(second)
    if not lengths > 0.0:
        return 0.0
    return math.degrees(math.acos(max(-1.0, min(1.0, _dot(first, second) / lengths))))
