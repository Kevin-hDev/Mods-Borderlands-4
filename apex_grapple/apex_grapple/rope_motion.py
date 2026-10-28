"""Our rope's shape at each frame, from the hand to the hook, and where each of its pieces lies along it.

The one formula for the rope's movement (docs/apex_grapple/pistolet-grappin/conception-mouvement-corde.md, Kevin,
2026-10-13): the grapple gun's look, Blender's videos of that dossier (outils/blender_rope_motion.py) and its trials
read this file, so that what Kevin chose on video is what the game shows. Moved here from the dossier on 2026-10-14,
when the look came into the mod, not copied. As Apex's rope does (enquetes/2026-10-13-corde-apex-en-mouvement.md of
that dossier): it hangs while the hook flies, swings and settles once the hook bites, runs straight while pulling,
and hangs again coming back. No game and no Blender here: lengths in cm, times in seconds, points as (x, y, z), z up.
"""

import math

# The three ways the rope hangs, shown to Kevin as videos G, H and I: the bow's depth as a share of the span from the
# hand to the hook, and its most in cm, so that a 100 m shot does not hang 10 m.
SLACKS = {"G": (0.03, 100.0), "H": (0.06, 200.0), "I": (0.10, 350.0)}
# The way the rope moves at first: Kevin's choice on the videos, seen in game; the three are the player's choice
# (the dossier's decisions.md, 13 October); settings.rope_movement's default.
SLACK_CHOSEN = "H"
# The wave along the hanging rope: its height as a share of the bow's depth, how many waves the rope holds, and how
# many pass a point each second, running toward the hook.
WAVE_SHARE, WAVE_TURNS, WAVE_RATE = 0.25, 1.5, 4.0
# Once the hook bites, the rope swings back and forth, dying out as exp(-t / SETTLE_S), one swing every SWING_S, and
# brought to nothing at SETTLED_S: Apex's rope is calm in about a third of a second.
SETTLE_S, SWING_S, SETTLED_S = 0.12, 0.2, 0.4
# Points along the rope, the hand's and the hook's included: odd so that one lies in the middle. 25 left sharp corners
# in the wave on Blender's videos (2026-10-13), seen from behind along a 22 m rope; the pieces are as many either way.
POINTS = 49


def _add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _scale(a, k):
    return tuple(x * k for x in a)


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _length(a):
    return math.sqrt(_dot(a, a))


def _across(along):
    """Across the rope: the way nearest straight down, the way beside it, and how much the first truly points down,
    from 1 on a level rope to 0 on one running straight up or down."""
    lying = _sub((0.0, 0.0, -1.0), _scale(along, -along[2]))
    hang = _length(lying)
    if hang < 1e-6:
        lying, hang = (1.0, 0.0, 0.0), 0.0
    below = _scale(lying, 1.0 / _length(lying))
    return below, _cross(along, below), hang


def swing(phase: str, since_s: float) -> float:
    """How much of the hanging shape shows: all of it while the hook flies out or comes back, a swing dying out once it
    bites, nothing while pulling. `since_s`: seconds since this phase began."""
    if phase in ("out", "back"):
        return 1.0
    if phase == "caught" and since_s < SETTLED_S:
        return (math.exp(-since_s / SETTLE_S) * math.cos(2.0 * math.pi * since_s / SWING_S)
                * (1.0 - since_s / SETTLED_S))
    return 0.0


def shape(hand, hook, slack: str, shown: float, clock_s: float) -> list[tuple[float, float, float]]:
    """The rope's POINTS points from the hand to the hook: the bow under the line between them and the wave running
    along it toward the hook, both `shown` strong (swing), nothing at either end. `clock_s`, seconds since the shot,
    moves the wave."""
    span = _sub(hook, hand)
    distance = _length(span)
    along = _scale(span, 1.0 / distance) if distance > 0.0 else (1.0, 0.0, 0.0)
    below, beside, hang = _across(along)
    share, most = SLACKS[slack]
    depth = min(share * distance, most) * shown
    # Written out rather than through _add and _scale, the same operations in the same order, so the same numbers to the
    # last bit: this runs at every frame of a shot, and the helpers cost some 300 calls a frame (review of 2026-10-24).
    hand_x, hand_y, hand_z = hand
    span_x, span_y, span_z = span
    below_x, below_y, below_z = below
    beside_x, beside_y, beside_z = beside
    points = []
    for number in range(POINTS):
        part = number / (POINTS - 1)
        envelope = math.sin(math.pi * part)
        wave = WAVE_SHARE * depth * envelope * math.sin(2.0 * math.pi * (WAVE_TURNS * part - WAVE_RATE * clock_s))
        bow = depth * hang * envelope
        points.append((hand_x + span_x * part + (below_x * bow + beside_x * wave),
                       hand_y + span_y * part + (below_y * bow + beside_y * wave),
                       hand_z + span_z * part + (below_z * bow + beside_z * wave)))
    return points


def laid(points, piece_cm: float) -> list[tuple[tuple[float, ...], tuple[float, ...]]]:
    """Where each piece lies along the points: as many pieces as fit best along the curve, each running straight from
    one place on it to the next, the places spread evenly along it; at least one."""
    # Written out as in shape(), the same numbers to the last bit. sum() and not +: since Python 3.12 it adds floats
    # compensated, which a chain of + does not, and _length went through sum().
    lengths = [math.sqrt(sum(((bx - ax) * (bx - ax), (by - ay) * (by - ay), (bz - az) * (bz - az))))
               for (ax, ay, az), (bx, by, bz) in zip(points, points[1:])]
    total = sum(lengths)
    count = max(1, round(total / piece_cm))
    places, segment, walked = [points[0]], 0, 0.0
    for number in range(1, count):
        mark = total * number / count
        while segment < len(lengths) - 1 and walked + lengths[segment] < mark:
            walked += lengths[segment]
            segment += 1
        share = (mark - walked) / lengths[segment] if lengths[segment] > 0.0 else 0.0
        (ax, ay, az), (bx, by, bz) = points[segment], points[segment + 1]
        places.append((ax + (bx - ax) * share, ay + (by - ay) * share, az + (bz - az) * share))
    places.append(points[-1])
    return list(zip(places, places[1:]))
