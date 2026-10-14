"""Where the grapple gun's hook is at each frame of a shot, and how much of the rope's hang shows: numbers in, positions
out, no game here (as release.py).

The hook leaves the hand whole, its base hole first at the hand, and flies at the hook's speed so that its point
reaches the aimed point, sunk in, at the very instant the pull starts: the flight's time is the grapple's own
(grapple.py). Once caught it stays planted, turned as it was at the catch. Let go, it comes back to the hand at the
same speed, base first, from wherever it was (docs/apex_grapple/pistolet-grappin/spec-pistolet-grappin.md, section 9,
choice 6), and the shot is over when it gets there. The rope runs from the hand to the hook's base. Lengths in cm,
times in ns as the grapple's clock gives them, rope_motion's phases.
"""

import math
from dataclasses import dataclass

NS_PER_S = 1_000_000_000
OUT, CAUGHT, BACK = "out", "caught", "back"


@dataclass
class Shot:
    """One shot of the grapple gun's look. `length`: the hook's base to its point; `sunk`: how deep its point goes;
    `speed`: the hook's, cm/s, out and back."""
    fired_ns: int
    flight_ns: int
    anchor: tuple[float, float, float]
    length: float
    sunk: float
    speed: float
    caught_ns: int | None = None
    planted: tuple | None = None
    released_ns: int | None = None
    released_from: tuple | None = None


def _toward(start, end):
    span = tuple(b - a for a, b in zip(start, end))
    distance = math.sqrt(sum(part * part for part in span))
    return tuple(part / distance for part in span) if distance > 0.0 else (1.0, 0.0, 0.0)


def _along(start, way, distance):
    return tuple(a + w * distance for a, w in zip(start, way))


def _planted(shot, hand):
    """The hook's base and way, its point `sunk` past the anchor along the line from `hand`."""
    way = _toward(hand, shot.anchor)
    return _along(shot.anchor, way, shot.sunk - shot.length), way


def where(shot: Shot, hand: tuple, now_ns: int) -> tuple | None:
    """(the hook's base, the way its point faces, the phase, seconds since that phase began), or None once it is back
    in the hand."""
    if shot.released_ns is not None:
        base_from = shot.released_from
        way = _toward(hand, base_from)
        left = math.dist(hand, base_from) - shot.speed * (now_ns - shot.released_ns) / NS_PER_S
        if left <= 0.0:
            return None
        return _along(hand, way, left), way, BACK, (now_ns - shot.released_ns) / NS_PER_S
    if shot.planted is not None:
        base, way = shot.planted
        return base, way, CAUGHT, (now_ns - shot.caught_ns) / NS_PER_S
    end, way = _planted(shot, hand)
    share = min(1.0, max(0.0, (now_ns - shot.fired_ns) / max(1, shot.flight_ns)))
    return tuple(h + (e - h) * share for h, e in zip(hand, end)), way, OUT, (now_ns - shot.fired_ns) / NS_PER_S


def catch(shot: Shot, hand: tuple, now_ns: int) -> None:
    """The hook bites: planted where its flight ends, turned as it faces now, until let go."""
    if shot.planted is None and shot.released_ns is None:
        shot.caught_ns, shot.planted = now_ns, _planted(shot, hand)


def release(shot: Shot, hand: tuple, now_ns: int) -> None:
    """Let go: the hook comes back from wherever it is."""
    if shot.released_ns is None:
        found = where(shot, hand, now_ns)
        shot.released_from = found[0] if found is not None else hand
        shot.released_ns = now_ns


def clock_s(shot: Shot, now_ns: int) -> float:
    """Seconds since the shot, which move the rope's wave."""
    return (now_ns - shot.fired_ns) / NS_PER_S
