"""How a trip to a starting point holds the player, the values measured in trials 95 to 97, each with its reason, the
one place in the mod they are written (docs/RUN/enquetes/2026-10-18-essai-95-points-de-depart.md). start_trip.py holds
the player by them; the cover (start_cover.py) gives up by HOLD_S and its own wait."""

import time

# Past this the place is not loading as it did: the floor came under Kevin's seven marks after 2.1 to 6.4 s (trial 97).
HOLD_S = 25.0
# Put back on the mark about once a frame, as the trials did (some 75 holds a second).
HOLD_EVERY_S = 0.01
# The floor looked for four times a second: a trace at every frame would cost for nothing while the place loads.
TRACE_EVERY_S = 0.25
# From just above the mark, the player's origin, about 1 m above his feet: under a low roof, a trace from higher meets
# the roof (trial 96).
MARK_UP_CM = 50.0
# Down to this far under it: the floor stood 0.9 to 1.0 m under the seven marks (trial 97); deeper is what lies under
# the map while the place loads.
MARK_DROP_CM = 250.0
# The same floor, to this much: the land under the map shows first while a place loads (trial 95), and the floor found
# must hold STABLE_S before the player is let go on it.
SAME_CM = 20.0
STABLE_S = 1.0
# The trip's clock is read at every image while a trip goes on: a longer gap between two readings is the game paused
# (its menu open on the black screen) or stalled, time left out, so that 25 s paused never ends a trip that has had no
# time to load (It Follows' audit, 2026-10-19). An image never takes this long while the game runs.
GAP_S = 0.5
_clock: dict = {"last": None, "left_out": 0.0}


def clock() -> float:
    """In seconds, the gaps of GAP_S and more left out; the tests move it."""
    now = time.monotonic()
    last, _clock["last"] = _clock["last"], now
    if last is not None and now - last >= GAP_S:
        _clock["left_out"] += now - last
    return now - _clock["left_out"]
