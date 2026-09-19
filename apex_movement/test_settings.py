"""Tests the settings: the defaults Kevin chose. The order between speeds is tested with speed_order."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from apex_movement import settings  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


switches = [settings.auto_sprint, settings.slides, settings.momentum_slides, settings.dash, settings.air_crouch,
            settings.air_strafe, settings.heavier_fall, settings.wall_climb]
check("every switch is on by default", all(option.value is True for option in switches))
check("the tuning sliders start at Kevin's values", (settings.air_acceleration.value, settings.fall_weight.value,
      settings.jump_height_bonus.value, settings.dash_distance.value) == (24000, 2.0, 20, 200))
check("the fall weight can still go heavier than its default: Kevin tried 2.1 in session 5",
      settings.fall_weight.args[1] > settings.fall_weight.value)
check("the Axle slide is off by default", settings.axle_slide.value is False)
check("its sliders start at Kevin's values: steering 350, 25 % faster, 50 % further on flat ground, 25 % on slopes",
      (settings.axle_steering.value, settings.axle_speed_boost.value, settings.axle_flat_distance_boost.value,
       settings.axle_slope_boost.value) == (350, 25, 50, 25))
check("the wall climb starts at Kevin's twice the height, 370 a second, a 60 degree diagonal and a 0.9 s wait",
      (settings.climb_height.value, settings.climb_speed.value, settings.climb_lean.value,
       settings.reclimb_delay.value) == (200, 370, 60, 0.9))
check("the slope boost cannot go far past Kevin's 25 %", settings.axle_slope_boost.args[:2] == (0, 50))

# mods_base loads a slider from the file without its bounds and keeps NaN (review, 2026-09-19).
settings.dash_distance.value = 10000
settings.fall_weight.value = 0.0
settings.walk_speed.value = float("nan")
settings.slide_speed.value = 1300
lines = settings.keep_in_bounds()
check("a hand-edited dash of 10000 percent goes back to the slider's 300: it made a 20 s dash",
      settings.dash_distance.value == 300)
check("a fall weight of 0 goes back to the slider's 1: it took gravity and every jump away",
      settings.fall_weight.value == 1.0)
check("a value that is not a number goes back to its default", settings.walk_speed.value == 672)
check("a value within its bounds is left alone", settings.slide_speed.value == 1300)
check("each value brought back is told once", len(lines) == 3 and any("dash_distance=10000" in line for line in lines))
check("the switches are left alone", settings.dash.value is True and settings.axle_slide.value is False)
check("nothing left to bring back, nothing told", settings.keep_in_bounds() == [])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
