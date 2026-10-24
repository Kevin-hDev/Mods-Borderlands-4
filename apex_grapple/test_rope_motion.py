"""Tests rope_motion.py: the rope hangs in a bow under the line from the hand to the hook, capped, none when it runs
straight up; a wave runs along it toward the hook; it swings and settles once the hook bites, runs straight while
pulling; and its pieces lie end to end along it."""

import importlib.util
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

# Loaded on its own, outside its package and with no fake SDK: the formula is numbers only.
_spec = importlib.util.spec_from_file_location("rope_motion", HERE / "apex_grapple" / "rope_motion.py")
motion = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(motion)

fails = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(a, b, within=1e-6):
    return all(abs(x - y) <= within for x, y in zip(a, b))


HAND = (100.0, 200.0, 300.0)
LEVEL = (1100.0, 200.0, 300.0)
middle = motion.POINTS // 2

straight = motion.shape(HAND, LEVEL, "H", 0.0, 0.3)
check("not shown, the rope runs straight from the hand to the hook, its points evenly spaced",
      len(straight) == motion.POINTS and near(straight[0], HAND) and near(straight[-1], LEVEL)
      and all(near(point, (100.0 + 1000.0 * n / (motion.POINTS - 1), 200.0, 300.0))
              for n, point in enumerate(straight)))

# The wave is nothing in the middle when 1.5 * 0.5 - 4 * clock is a whole half: at clock 0.0625 s.
hanging = motion.shape(HAND, LEVEL, "H", 1.0, 0.0625)
check("a level rope hangs straight down in the middle by its share of the span, 6 % of 10 m at H, the ends held",
      near(hanging[middle], (600.0, 200.0, 240.0)) and near(hanging[0], HAND) and near(hanging[-1], LEVEL, 1e-9)
      and all(point[2] <= 300.0 + 1e-9 for point in hanging))
check("the bow is deepest in the middle and the same on both sides of it",
      min(range(motion.POINTS), key=lambda n: hanging[n][2]) == middle
      and all(abs(hanging[n][2] - hanging[-1 - n][2]) < 1e-9 for n in range(motion.POINTS)))
far = motion.shape(HAND, (10100.0, 200.0, 300.0), "H", 1.0, 0.0625)
check("on a 100 m shot the bow stops at its most, 2 m at H, not 6 m",
      abs(far[middle][2] - (300.0 - 200.0)) < 1e-6)
check("Kevin's choice is H, one of the three", motion.SLACK_CHOSEN == "H" and motion.SLACK_CHOSEN in motion.SLACKS)
check("G hangs less than H, H less than I",
      [motion.shape(HAND, LEVEL, slack, 1.0, 0.0625)[middle][2] for slack in "GHI"] == [270.0, 240.0, 200.0])

up = motion.shape(HAND, (100.0, 200.0, 1300.0), "I", 1.0, 0.1)
check("a rope running straight up does not hang: only the wave moves it, beside it",
      all(abs(point[0] - 100.0) < 1e-9 for point in up) and any(abs(point[1] - 200.0) > 1.0 for point in up))
slanted = motion.shape(HAND, (1100.0, 200.0, 1300.0), "H", 1.0, 0.0625)
check("a rope climbing at 45 degrees hangs less than a level one, by the sine of its angle to the upright",
      abs(math.dist(slanted[middle], (600.0, 200.0, 800.0)) - 0.06 * 1000.0 * math.sqrt(2.0) * math.sqrt(0.5)) < 1e-6)


def beside(clock_s, number):
    return motion.shape(HAND, LEVEL, "H", 1.0, clock_s)[number][1] - 200.0


# Where 1.5 * part - 4 * clock is a whole half the wave is nothing: in the middle at 0.0625 s, and one point further on
# toward the hook once the wave has run that point's share of the rope, 1.5 / (POINTS - 1) / 4 s later.
step_s = 1.5 / (motion.POINTS - 1) / 4
check("the wave runs beside the level rope, a quarter of the bow high at most, and toward the hook",
      max(abs(point[1] - 200.0) for point in hanging) <= 0.25 * 60.0 + 1e-9
      and abs(beside(0.0625, middle)) < 1e-9 and abs(beside(0.0625 + step_s, middle + 1)) < 1e-9
      and abs(beside(0.0625, middle + 1)) > 1.0)

check("the shape shows whole while the hook flies out and comes back, not while pulling",
      motion.swing("out", 0.0) == motion.swing("out", 5.0) == motion.swing("back", 1.0) == 1.0
      and motion.swing("pulling", 0.0) == 0.0)
swings = [motion.swing("caught", t / 100.0) for t in range(0, 45)]
check("once the hook bites it starts whole, swings past the line, dies out and is nothing from 0.4 s on",
      swings[0] == 1.0 and swings[10] < -0.1 and max(abs(one) for one in swings[30:]) < 0.05
      and swings[40:] == [0.0] * 5)

pieces = motion.laid(straight, 45.6)
check("straight, as many pieces as fit best, 22 of 45.5 cm for 10 m, end to end from the hand to the hook",
      len(pieces) == 22 and near(pieces[0][0], HAND) and near(pieces[-1][1], LEVEL)
      and all(near(one[1], two[0]) for one, two in zip(pieces, pieces[1:]))
      and all(abs(math.dist(*one) - 1000.0 / 22) < 1e-6 for one in pieces))
bowed = motion.shape(HAND, LEVEL, "I", 1.0, 0.0625)
along = sum(math.dist(a, b) for a, b in zip(bowed, bowed[1:]))
curved = motion.laid(bowed, 45.6)
check("hanging, the pieces follow the curve, as many as its length holds, each from one point on it to the next",
      len(curved) == round(along / 45.6) and near(curved[0][0], HAND) and near(curved[-1][1], LEVEL, 1e-9)
      and all(near(one[1], two[0]) for one, two in zip(curved, curved[1:]))
      and min(point[2] for one in curved for point in one) < 300.0 - 90.0)
check("a rope of nothing is one piece of nothing",
      motion.laid(motion.shape(HAND, HAND, "H", 1.0, 0.0), 45.6) == [(HAND, HAND)])

# 2026-10-24 review: the formula ran at every frame of a shot through some 300 small vector helpers. Written out in the
# loops, it must give the very same numbers, to the last bit, as the formula Kevin chose on video: this copy of it is
# kept frozen here as the reference.
def _frozen_shape(hand, hook, slack, shown, clock_s):
    def add(a, b):
        return tuple(x + y for x, y in zip(a, b))

    def scale(a, k):
        return tuple(x * k for x in a)

    span = tuple(x - y for x, y in zip(hook, hand))
    distance = math.sqrt(sum(x * x for x in span))
    along = scale(span, 1.0 / distance) if distance > 0.0 else (1.0, 0.0, 0.0)
    below, beside, hang = motion._across(along)
    share, most = motion.SLACKS[slack]
    depth = min(share * distance, most) * shown
    points = []
    for number in range(motion.POINTS):
        part = number / (motion.POINTS - 1)
        envelope = math.sin(math.pi * part)
        wave = (motion.WAVE_SHARE * depth * envelope
                * math.sin(2.0 * math.pi * (motion.WAVE_TURNS * part - motion.WAVE_RATE * clock_s)))
        off = add(scale(below, depth * hang * envelope), scale(beside, wave))
        points.append(add(add(hand, scale(span, part)), off))
    return points


def _frozen_laid(points, piece_cm):
    lengths = [math.sqrt(sum(x * x for x in (q - p for p, q in zip(a, b)))) for a, b in zip(points, points[1:])]
    total = sum(lengths)
    count = max(1, round(total / piece_cm))
    places, segment, walked = [points[0]], 0, 0.0
    for number in range(1, count):
        mark = total * number / count
        while segment < len(lengths) - 1 and walked + lengths[segment] < mark:
            walked += lengths[segment]
            segment += 1
        share = (mark - walked) / lengths[segment] if lengths[segment] > 0.0 else 0.0
        step = tuple(q - p for p, q in zip(points[segment], points[segment + 1]))
        places.append(tuple(p + s * share for p, s in zip(points[segment], step)))
    places.append(points[-1])
    return list(zip(places, places[1:]))


same = True
for hook in ((100.0, 200.0, 300.0), (2300.0, -517.25, 412.5), (100.0, 200.0, 4300.0), (-7350.75, 9120.0, -260.0),
             (100.0001, 200.0, 300.0)):
    for slack in motion.SLACKS:
        for shown in (0.0, 0.37, 1.0, -0.42):
            for clock_s in (0.0, 0.016, 1.3337):
                points = motion.shape(HAND, hook, slack, shown, clock_s)
                frozen = _frozen_shape(HAND, hook, slack, shown, clock_s)
                same = same and points == frozen
                for piece_cm in (45.6, 54.72, 31.92):
                    same = same and motion.laid(points, piece_cm) == _frozen_laid(frozen, piece_cm)
check("the curve and the pieces' places are the formula's to the last bit, at every reach, slack and moment", same)

calls = []
for helper in ("_add", "_sub", "_scale", "_dot"):
    held = getattr(motion, helper)
    setattr(motion, helper, lambda *args, _held=held: (calls.append(1), _held(*args))[1])
pieces = motion.laid(motion.shape(HAND, (2300.0, -517.25, 412.5), "H", 1.0, 0.5), 45.6)
check("and they take a handful of small helpers, not one per point", len(pieces) > 40 and len(calls) < 10)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
