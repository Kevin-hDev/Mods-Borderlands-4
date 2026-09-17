"""Tests the menu: defaults Kevin chose, and the speed order kept whatever the sliders say."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import settings  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


defaults = settings.speeds()
check("the default speeds are Kevin's table", defaults == settings.Speeds(672.0, 960.0, 1130.0, 550.0))
switches = [settings.auto_sprint, settings.momentum_slides, settings.air_crouch, settings.air_strafe, settings.heavier_fall,
            settings.wall_climb]
check("every switch is on by default", all(option.value is True for option in switches))
check("the tuning sliders start at Kevin's values", (settings.air_acceleration.value, settings.fall_weight.value,
      settings.jump_height_bonus.value, settings.dash_distance.value) == (24000, 1.6, 20, 200))
check("the Axle slide is off by default", settings.axle_slide.value is False)
check("its sliders start at Kevin's values: steering 350, 25 % faster, 50 % further on flat ground, 25 % on slopes",
      (settings.axle_steering.value, settings.axle_speed_boost.value, settings.axle_flat_distance_boost.value,
       settings.axle_slope_boost.value) == (350, 25, 50, 25))
check("the wall climb starts at Kevin's twice the height, 370 a second, a 60 degree diagonal and a 1.2 s wait",
      (settings.climb_height.value, settings.climb_speed.value, settings.climb_lean.value,
       settings.reclimb_delay.value) == (200, 370, 60, 1.2))
check("the slope boost cannot go far past Kevin's 25 %", settings.axle_slope_boost.args[:2] == (0, 50))

slow_sprint = settings.ordered(800.0, 700.0, 1080.0, 550.0)
check("a sprint below the walk is raised to the walk", slow_sprint.sprint == 800.0)
slow_slide = settings.ordered(672.0, 960.0, 900.0, 550.0)
check("a slide below the sprint is raised to the sprint", slow_slide.slide == 960.0)
high_minimum = settings.ordered(672.0, 960.0, 1080.0, 1500.0)
check("a landing slide minimum above the sprint is lowered to it", high_minimum.landing_slide_min == 960.0)
chained = settings.ordered(1000.0, 500.0, 400.0, 2000.0)
check("the order holds through a chain of low values", (chained.sprint, chained.slide, chained.landing_slide_min) == (1000.0, 1000.0, 1000.0))

settings.walk_speed.value = 700
check("speeds follow the sliders", settings.speeds().walk == 700.0)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
