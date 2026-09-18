"""Tests the speed order: Kevin's defaults, the order kept whatever the sliders say, and what a separate file compares
against when it does not carry the speeds."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import pack, settings, slide_physics, speed_order  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("the default speeds are Kevin's table",
      speed_order.speeds() == speed_order.Speeds(672.0, 960.0, 1130.0, 550.0, 2000.0))

slow_sprint = speed_order.ordered(800.0, 700.0, 1080.0, 550.0, 2000.0)
check("a sprint below the walk is raised to the walk", slow_sprint.sprint == 800.0)
slow_slide = speed_order.ordered(672.0, 960.0, 900.0, 550.0, 2000.0)
check("a slide below the sprint is raised to the sprint", slow_slide.slide == 960.0)
high_minimum = speed_order.ordered(672.0, 960.0, 1080.0, 1500.0, 2000.0)
check("a landing slide minimum above the sprint is lowered to it", high_minimum.landing_slide_min == 960.0)
chained = speed_order.ordered(1000.0, 500.0, 400.0, 2000.0, 600.0)
check("the order holds through a chain of low values",
      (chained.sprint, chained.slide, chained.landing_slide_min, chained.slide_max) == (1000.0, 1000.0, 1000.0, 1000.0))
# A top speed under the start speed: the slide started at 2500 and dropped to 500 within its first frame (review).
low_top = speed_order.ordered(672.0, 960.0, 2500.0, 550.0, 500.0)
check("a top slide speed below the start speed is raised to it", low_top.slide_max == 2500.0)
# A slide started at or under the speed where the mod ends a slide was cancelled on its first frame (review). The
# slider lives in settings, which cannot import slide_physics, so the relation is held here.
check("the slide speed slider cannot go down to where a slide is ended at once",
      settings.slide_speed.args[0] > slide_physics.STOP_SPEED)

settings.walk_speed.value = 700
check("speeds follow the sliders", speed_order.speeds().walk == 700.0)
settings.walk_speed.value = 672

# A separate file keeps its own settings and cannot see another file's: without the speeds, it orders its slide
# against the game's own sprint, not against a slider that is not in its menu and never loads (review, 2026-09-18).
pack.CARRIES = ("Slides",)
settings.sprint_speed.value = 1500
settings.slide_speed.value = 900
apart = speed_order.speeds()
check("a file without the speeds orders against the game's own walk and sprint",
      (apart.walk, apart.sprint) == (speed_order.GAME_WALK, speed_order.GAME_SPRINT))
check("so a slide set under the unseen sprint slider is not silently raised to it", apart.slide == 900.0)
pack.CARRIES = ()
check("the full pack orders against its own sliders", speed_order.speeds().slide == 1500.0)
settings.sprint_speed.value = 960
settings.slide_speed.value = 1130

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
