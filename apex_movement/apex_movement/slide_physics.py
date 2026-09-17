"""Apex-style slides: a slide slows down by friction, a steep enough slope cancels it, and it ends when it runs out of
speed, instead of following the game's timer.

Kevin, 2026-09-17: in Apex a slide down a steep slope never loses speed and stops once the ground flattens; in BL4 it
slows down anyway (1341 down to 475 in 1.7 s on a 14 degree slope). Flat ground must keep today's distance, uphill
must be shorter. What the game lets a mod do was measured the same day (02:05-02:07): Move_Slide's speed curve is read
every frame, Duration lengthens a slide, and SetWantsToSlide(False) ends one on the next frame. So while the mod runs,
Duration is long enough never to end a slide, the game's slope effect is neutral (the mod applies the slope itself),
and every frame of a slide the speed curve is set flat to the speed this module computes.

An Axle slide (axle_slide.py) starts faster and slows down, or speeds up downhill, by a factor that makes its distance
the boosted one: a slide's distance is (start speed squared - stop speed squared) / (2 x slowdown), so starting faster
already goes further by that ratio of squares, and the slowdown is scaled by that ratio over the distance wanted.

The slope effect is neutralised by flattening SpeedSlopeScaleCurve to 1, not by switching bUseSlopeCurve off: with
bUseSlopeCurve off every slide ended after 6 to 9 ms, while Duration 10 and 30 s worked (verified in game, 2026-09-17,
02:53-02:54).
"""

import math
from dataclasses import dataclass
from typing import Any

from . import axle_slide, game, ownership, report, settings

DURATION_KEY = "Move_Slide.Duration.constant"
CURVE_KEY = "Move_Slide.SpeedScaleCurve"
SLOPE_CURVE_KEY = "Move_Slide.SpeedSlopeScaleCurve"
# Only a far safety net: slides end when the mod ends them.
LONG_DURATION = 30.0
# The game's own slides ended at 316 to 568 (2026-09-17, 02:05): below this a slide has run out of speed.
STOP_SPEED = 350.0
# A frame longer than this, such as a hitch while loading, is counted as this long.
MAX_STEP_S = 0.1
TOLERANCE = 1e-4


@dataclass(frozen=True)
class Curve:
    values: tuple[float, ...]
    arrive: tuple[float, ...]
    leave: tuple[float, ...]


_prepared: Any = None
_slide: dict[str, Any] | None = None


def reset() -> None:
    global _prepared, _slide
    _prepared, _slide = None, None


def friction(start_speed: float, distance: float) -> float:
    """The steady slowdown that takes a slide from its start speed to STOP_SPEED over the distance on flat ground."""
    return max((start_speed ** 2 - STOP_SPEED ** 2) / (2.0 * max(distance, 1.0)), 1.0)


def downhill(normal: Any, velocity: Any) -> float:
    """Slope along the slide, positive going down: a floor that falls away ahead tilts its normal forward."""
    speed = math.hypot(velocity.X, velocity.Y)
    if speed < 1.0:
        return 0.0
    return (normal.X * velocity.X + normal.Y * velocity.Y) / speed


def next_speed(speed: float, step_s: float, slope: float, slowdown: float, pull: float, top: float,
               scale: float = 1.0) -> float:
    return min(max(speed + scale * (pull * slope - slowdown) * step_s, 0.0), top)


def speed_gain(normal_start: float, boost: axle_slide.Boost) -> float:
    """How many times further a slide goes for starting at the boosted speed, slowing down as a normal slide."""
    boosted = normal_start * boost.speed
    return max(boosted ** 2 - STOP_SPEED ** 2, 1.0) / max(normal_start ** 2 - STOP_SPEED ** 2, 1.0)


def _keys(asset: Any, name: str = "SpeedScaleCurve") -> Any:
    return getattr(asset, name).EditorCurveData.keys


def _read_curve(asset: Any, name: str) -> Curve:
    keys = list(_keys(asset, name))
    return Curve(tuple(float(key.Value) for key in keys), tuple(float(key.ArriveTangent) for key in keys),
                 tuple(float(key.LeaveTangent) for key in keys))


def _put_curve(name: str, curve: Curve) -> None:
    # Written in place through the array's views, verified in game on 2026-09-17 for the speed curve.
    for key, value, arrive, leave in zip(_keys(game.slide_asset(), name), curve.values, curve.arrive, curve.leave):
        key.Value, key.ArriveTangent, key.LeaveTangent = value, arrive, leave


def _flat(value: float, count: int) -> Curve:
    return Curve((value,) * count, (0.0,) * count, (0.0,) * count)


def _set_flat(asset: Any, value: float) -> None:
    for key in _keys(asset):
        key.Value = value


def _put_duration(value: float) -> None:
    asset = game.slide_asset()
    duration = asset.Duration
    duration.constant = value
    # Assigned back whole: the SDK may hand out a copy of the struct, and a field written on a copy changes nothing.
    asset.Duration = duration


def _prepare(asset: Any) -> None:
    """Once per slide asset: long Duration, slope curve flat at 1, speed curve flat at its start value, no tangents.

    Tangents are slopes between points; left as they were, a curve with equal values still dipped between its points
    (1123 then 1085 at 800 and 1200 ms instead of 1130, 2026-09-17).
    """
    global _prepared
    if ownership.is_owned(CURVE_KEY):
        game_curve = ownership.original(CURVE_KEY)
    else:
        game_curve = _read_curve(asset, "SpeedScaleCurve")
    ownership.write(CURVE_KEY, ownership.ASSET, lambda: _read_curve(game.slide_asset(), "SpeedScaleCurve"),
                    lambda curve: _put_curve("SpeedScaleCurve", curve), _flat(game_curve.values[0], len(game_curve.values)))
    slope_points = len(list(_keys(asset, "SpeedSlopeScaleCurve")))
    ownership.write(SLOPE_CURVE_KEY, ownership.ASSET, lambda: _read_curve(game.slide_asset(), "SpeedSlopeScaleCurve"),
                    lambda curve: _put_curve("SpeedSlopeScaleCurve", curve), _flat(1.0, slope_points))
    ownership.write(DURATION_KEY, ownership.ASSET, lambda: float(game.slide_asset().Duration.constant), _put_duration,
                    LONG_DURATION)
    _prepared = asset
    report.note(f"slide physics on: duration {LONG_DURATION:.0f} s, slope curve flat at 1, speed curve flat at "
                f"{game_curve.values[0]:.4f}")


def _start(now_ns: int) -> dict[str, Any]:
    # Read once: an Axle slide switched on or off mid-slide keeps the boost it started with, like its start speed.
    boost = axle_slide.current()
    normal_start = settings.speeds().slide
    start_speed = normal_start * boost.speed
    # slide.py sets the speed constant so that the curve's first value gives the slide speed (892 x 1.15 x 1.1017 =
    # 1130, verified): the speed per unit of curve is that ratio, read without the ground speed bonus, which is only
    # known to be right while standing.
    per_unit = start_speed / max(ownership.original(CURVE_KEY).values[0], TOLERANCE)
    return {"start_ns": now_ns, "last_ns": now_ns, "per_unit": per_unit,
            "speed": start_speed, "top": start_speed, "slope_sum": 0.0, "ground_frames": 0, "ended": False,
            "ratio_sum": 0.0, "ratio_frames": 0, "boost": boost, "gain": speed_gain(normal_start, boost),
            "slowdown": friction(normal_start, float(settings.slide_distance.value))}


def _finish(asset: Any, movement: Any, now_ns: int) -> None:
    global _slide
    slide, _slide = _slide, None
    _set_flat(asset, ownership.original(CURVE_KEY).values[0])
    slope = slide["slope_sum"] / slide["ground_frames"] if slide["ground_frames"] else 0.0
    ratio = f"{slide['ratio_sum'] / slide['ratio_frames']:.2f}" if slide["ratio_frames"] else "-"
    boost = slide["boost"]
    report.note(f"slide physics end ms={(now_ns - slide['start_ns']) // 1_000_000} by={'mod' if slide['ended'] else 'game'} "
                f"model_speed={slide['speed']:.0f} game_speed={game.horizontal_speed(movement):.0f} "
                f"game_to_model={ratio} top={slide['top']:.0f} slope_avg={slope:+.2f} "
                f"axle={boost.speed:.2f}/{boost.flat:.2f}/{boost.slope:.2f}")


def update(character: Any, now_ns: int) -> None:
    global _slide
    asset = game.slide_asset()
    if asset is None:
        report.error_once("slide_asset", "Move_Slide not found yet; slides keep the game's own speed meanwhile")
        return
    if _prepared is not asset:
        _prepare(asset)
    movement = character.CharacterMovement
    if not game.is_sliding(movement):
        if _slide is not None:
            _finish(asset, movement, now_ns)
        return
    if _slide is None:
        _slide = _start(now_ns)
    slide = _slide
    step_s = min((now_ns - slide["last_ns"]) / 1e9, MAX_STEP_S)
    slide["last_ns"] = now_ns
    # In the air, off a ramp, the game keeps the slide going: nothing rubs and no slope pulls.
    if game.is_on_ground(movement):
        if slide["ground_frames"] > 0 and not slide["ended"]:
            # The game's speed this frame came from last frame's curve: compared with the model speed written then.
            slide["ratio_sum"] += game.horizontal_speed(movement) / max(slide["speed"], 1.0)
            slide["ratio_frames"] += 1
        hit = movement.CurrentFloor.HitResult
        slope = downhill(hit.ImpactNormal, movement.Velocity)
        slide["slope_sum"] += slope
        slide["ground_frames"] += 1
        slide["speed"] = next_speed(slide["speed"], step_s, slope, slide["slowdown"],
                                    float(settings.slide_downhill_pull.value),
                                    float(settings.slide_max_speed.value) * slide["boost"].speed,
                                    slide["gain"] / axle_slide.distance(slide["boost"], slope))
        slide["top"] = max(slide["top"], slide["speed"])
    if slide["speed"] <= STOP_SPEED and not slide["ended"]:
        slide["ended"] = True
        character.SetWantsToSlide(False)
    _set_flat(asset, slide["speed"] / slide["per_unit"])


def stop(character: Any) -> None:
    owned = ownership.is_owned(CURVE_KEY)
    reset()
    for key in (CURVE_KEY, SLOPE_CURVE_KEY, DURATION_KEY):
        ownership.restore(key)
    if owned:
        report.note("slide physics off, game slide timer and curves restored")
