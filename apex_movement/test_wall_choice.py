"""Tests which surface a climb judges itself on, out of what the traces met at their heights: the nearest upright one,
merged with the other views of the same wall, or else the nearest of all so a refusal can describe it."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from apex_movement import wall_choice  # noqa: E402
from apex_movement.climb_aim import Wall  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def pick(*walls: Wall) -> Wall | None:
    return wall_choice.best_wall(list(walls))


PANEL = Wall(distance=98.0, into_x=1.0, into_y=0.0, flat=1.0)
BEVEL = Wall(distance=2.0, into_x=1.0, into_y=0.0, flat=0.53)
NEARER = Wall(distance=60.0, into_x=1.0, into_y=0.0, flat=0.80)

check("nothing met, nothing picked", pick() is None)
check("a bevel at arm's length does not hide the panel behind it: it is not upright enough to be a wall",
      pick(BEVEL, PANEL) is PANEL)
just_upright = Wall(distance=50.0, into_x=1.0, into_y=0.0, flat=0.7)
check("a face just upright enough is a wall, and the nearest one is taken", pick(just_upright, PANEL).distance == 50.0)
merged = pick(PANEL, NEARER)
check("two heights seeing the same wall are merged: its nearest distance, its best uprightness",
      merged.distance == 60.0 and merged.flat == 1.0)
SIDE = Wall(distance=70.0, into_x=0.0, into_y=1.0, flat=1.0)
check("a wall facing another way is not merged in: the nearest one alone is taken",
      pick(NEARER, SIDE) is NEARER)
bar = Wall(distance=50.0, into_x=0.94, into_y=0.34, flat=0.9)
smoothed = pick(bar, NEARER)
check("a bar standing proud of the face is smoothed into it, not followed on its own",
      round(smoothed.into_x, 2) == 0.98 and round(smoothed.into_y, 2) == 0.17)
check("with no upright surface at all, the nearest is picked so a refusal can describe it",
      pick(BEVEL, Wall(distance=9.0, into_x=1.0, into_y=0.0, flat=0.2)) is BEVEL)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
