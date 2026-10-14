"""Tests look_timing.py: the hook leaves the hand whole and its point reaches the aimed point, sunk in, at the end of
its flight; it stays planted as it was turned at the catch; let go, it comes back at the hook's speed, from the
planted point or from mid-flight, and the shot ends in the hand; at the settings' bounds (5 and 100 m, 10 and
300 m/s)."""

import importlib.util
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

# Loaded on its own, outside its package and with no fake SDK: the timing is numbers only.
_spec = importlib.util.spec_from_file_location("look_timing", HERE / "apex_grapple" / "look_timing.py")
timing = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(timing)

fails = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(a, b, within=1e-6):
    return all(abs(x - y) <= within for x, y in zip(a, b))


S = timing.NS_PER_S
HAND = (0.0, 0.0, 100.0)
LENGTH, SUNK = 15.68, 1.5


def shot(distance_cm, speed_cm_s, fired_ns=10 * S):
    flight_ns = int(distance_cm / speed_cm_s * S)
    return timing.Shot(fired_ns, flight_ns, (distance_cm, 0.0, 100.0), LENGTH, SUNK, speed_cm_s)


one = shot(3000.0, 5000.0)
base, way, phase, since = timing.where(one, HAND, one.fired_ns)
check("at the shot, the hook's base is in the hand, its point toward the aimed point, flying out",
      near(base, HAND) and near(way, (1.0, 0.0, 0.0)) and phase == timing.OUT and since == 0.0)
base, _, _, _ = timing.where(one, HAND, one.fired_ns + one.flight_ns // 2)
end = 3000.0 + SUNK - LENGTH
check("halfway through its flight, halfway to where it bites", abs(base[0] - end / 2) < 1e-3)
base, way, phase, _ = timing.where(one, HAND, one.fired_ns + one.flight_ns)
tip = tuple(b + w * LENGTH for b, w in zip(base, way))
check("at the end of its flight, its point is in the aimed point, sunk 1.5 cm", near(tip, (3000.0 + SUNK, 0.0, 100.0))
      and phase == timing.OUT)
base, _, _, _ = timing.where(one, HAND, one.fired_ns + 3 * one.flight_ns)
check("it never flies past it", abs(base[0] - end) < 1e-6)

timing.catch(one, HAND, one.fired_ns + one.flight_ns)
moved = (500.0, 400.0, 300.0)
base, way, phase, since = timing.where(one, moved, one.fired_ns + one.flight_ns + S // 4)
check("caught, it stays planted and turned as at the catch, whatever the hand does",
      near(base, (end, 0.0, 100.0)) and near(way, (1.0, 0.0, 0.0)) and phase == timing.CAUGHT
      and abs(since - 0.25) < 1e-9)
check("the rope's wave counts from the shot", abs(timing.clock_s(one, one.fired_ns + 2 * S) - 2.0) < 1e-9)

let_go = one.fired_ns + one.flight_ns + S
timing.release(one, HAND, let_go)
base, way, phase, since = timing.where(one, HAND, let_go + S // 10)
check("let go, it comes back from the planted point at the hook's speed, base first", phase == timing.BACK
      and abs(math.dist(HAND, base) - (end - 500.0)) < 1e-3 and near(way, (1.0, 0.0, 0.0)) and abs(since - 0.1) < 1e-9)
check("and the shot ends in the hand after the distance at that speed",
      timing.where(one, HAND, let_go + int(end / 5000.0 * S) - S // 1000) is not None
      and timing.where(one, HAND, let_go + int(end / 5000.0 * S) + S // 1000) is None)
timing.catch(one, HAND, let_go + S // 10)
timing.release(one, HAND, let_go + S // 5)
check("once let go, neither a catch nor a second release changes its way back",
      one.planted is not None and one.released_ns == let_go)

cancelled = shot(3000.0, 5000.0)
timing.release(cancelled, HAND, cancelled.fired_ns + cancelled.flight_ns // 2)
check("called off in flight, it comes back from where it flew to",
      abs(cancelled.released_from[0] - end / 2) < 1e-3 and cancelled.planted is None)

for distance, speed, back_s in ((500.0, 1000.0, 0.5), (10000.0, 1000.0, 10.0), (500.0, 30000.0, 1 / 60),
                                (10000.0, 30000.0, 1 / 3)):
    bound = shot(distance, speed)
    timing.catch(bound, HAND, bound.fired_ns + bound.flight_ns)
    timing.release(bound, HAND, bound.fired_ns + bound.flight_ns)
    gone = bound.fired_ns + bound.flight_ns + int((distance + SUNK - LENGTH) / speed * S)
    check(f"at {distance / 100:g} m and {speed / 100:g} m/s, back in {back_s:.2f} s",
          timing.where(bound, HAND, gone - S // 1000) is not None
          and timing.where(bound, HAND, gone + S // 1000) is None
          and abs((gone - bound.released_ns) / S - (distance + SUNK - LENGTH) / speed) < 1e-6)

instant = timing.Shot(5 * S, 0, (1000.0, 0.0, 100.0), LENGTH, SUNK, 5000.0)
check("a flight of no time puts the hook at its point the next instant",
      timing.where(instant, HAND, 5 * S + 1)[0][0] > 900.0)
on_hand = timing.Shot(5 * S, S, HAND, LENGTH, SUNK, 5000.0)
check("an aimed point in the hand itself still gives a hook, never a division by zero",
      timing.where(on_hand, HAND, 5 * S) is not None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
