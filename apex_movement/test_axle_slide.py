"""Tests the Axle slide numbers: no boost while off, boosts from the sliders, flat boost giving way to the slope boost."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import axle_slide, settings  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(a: float, b: float) -> bool:
    return abs(a - b) < 1e-9


check("the Axle slide is off by default, so no boost", axle_slide.current() == axle_slide.NONE)
check("a normal slide starts at the slide speed", near(axle_slide.start_speed(), 1130.0))
check("without a boost every ground gives the normal distance",
      all(near(axle_slide.distance(axle_slide.NONE, slope), 1.0) for slope in (-0.3, -0.07, 0.0, 0.07, 0.3)))

settings.axle_slide.value = True
boost = axle_slide.current()
check("switched on, the boosts are Kevin's: 25 % faster, 50 % further on flat ground, 25 % further on slopes",
      boost == axle_slide.Boost(speed=1.25, flat=1.5, slope=1.25))
check("an Axle slide starts 25 % faster", near(axle_slide.start_speed(), 1412.5))
check("flat ground gets the flat boost", near(axle_slide.distance(boost, 0.0), 1.5))
check("slopes read on flat ground still count as flat", near(axle_slide.distance(boost, -0.05), 1.5)
      and near(axle_slide.distance(boost, 0.05), 1.5))
check("a gentle slope is between the two", near(axle_slide.distance(boost, 0.075), 1.375)
      and near(axle_slide.distance(boost, -0.075), 1.375))
check("a real slope, uphill or downhill, gets the slope boost", near(axle_slide.distance(boost, 0.1), 1.25)
      and near(axle_slide.distance(boost, -0.28), 1.25))

settings.axle_speed_boost.value = 0
settings.axle_flat_distance_boost.value = 200
settings.axle_slope_boost.value = 50
check("the boosts follow the sliders", axle_slide.current() == axle_slide.Boost(speed=1.0, flat=3.0, slope=1.5))
settings.slide_speed.value = 1200
check("the start follows the normal slide speed", near(axle_slide.start_speed(), 1200.0))

settings.axle_slide.value = False
check("switched off again, the sliders no longer count", axle_slide.current() == axle_slide.NONE)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
