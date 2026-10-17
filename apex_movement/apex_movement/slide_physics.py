"""Apex-style slides: a slide slows down by friction, a steep enough slope cancels it, and it ends when it runs out of
speed, instead of following the game's timer.

Kevin, 2026-09-17: in Apex a slide down a steep slope never loses speed and stops once the ground flattens; in BL4 it
slows down anyway (1341 down to 475 in 1.7 s on a 14 degree slope). Flat ground must keep today's distance, uphill
must be shorter. So while the mod runs, Duration is long enough never to end a slide, the game's slope effect is
neutral (the model applies the slope itself, slide_model.py), and SetWantsToSlide(False) ends a slide once out of
speed (all three verified in game on 2026-09-17).

The speed goes through the sliding character's own speed scale, which the game multiplies a slide by every frame
(halved mid-slide, the speed halved within 100 ms on four slides, verified in game on 2026-10-16,
releves/coop/2026-10-16-glissade-echelle). Until then the speed curve of Move_Slide was rewritten every frame; but
Move_Slide is shared by every character of a machine, so a co-op host computed its guests' slides without any slowdown
and pulled them forward. The curve now stays flat, and the host runs one model per guest on that guest's scale.

The slope effect is neutralised by flattening SpeedSlopeScaleCurve to 1, not by switching bUseSlopeCurve off: with
bUseSlopeCurve off every slide ended after 6 to 9 ms, while Duration 10 and 30 s worked (verified in game, 2026-09-17,
02:53-02:54).
"""

from dataclasses import dataclass
from typing import Any

from . import axle_slide, game, ownership, report, settings, slide, slide_model, speed_order

DURATION_KEY = "Move_Slide.Duration.constant"
CURVE_KEY = "Move_Slide.SpeedScaleCurve"
SLOPE_CURVE_KEY = "Move_Slide.SpeedSlopeScaleCurve"
GUEST_FIELD = "MaxGroundSpeedScale.Value"
GUEST_MEMO = "slide"


@dataclass(frozen=True)
class Curve:
    values: tuple[float, ...]
    arrive: tuple[float, ...]
    leave: tuple[float, ...]


_prepared: Any = None
_slide: slide_model.Model | None = None
# Set by a frame without a slide: only a slide begun after it gets the model.
_armed = False


def reset() -> None:
    global _prepared, _slide, _armed
    _prepared, _slide, _armed = None, None, False
    speed_order.hold_scale_for_slide(False)


def _keys(asset: Any, name: str = "SpeedScaleCurve") -> Any:
    return getattr(asset, name).EditorCurveData.keys


def _read_curve(asset: Any, name: str) -> Curve:
    keys = list(_keys(asset, name))
    return Curve(tuple(float(key.Value) for key in keys), tuple(float(key.ArriveTangent) for key in keys),
                 tuple(float(key.LeaveTangent) for key in keys))


def _put_curve(name: str, curve: Curve) -> None:
    # Written in place through the array's views, verified in game on 2026-09-17 for the speed curve.
    keys = _keys(ownership.loaded(game.slide_asset()), name)
    for key, value, arrive, leave in zip(keys, curve.values, curve.arrive, curve.leave):
        key.Value, key.ArriveTangent, key.LeaveTangent = value, arrive, leave


def _flat(value: float, count: int) -> Curve:
    return Curve((value,) * count, (0.0,) * count, (0.0,) * count)


def _put_duration(value: float) -> None:
    asset = ownership.loaded(game.slide_asset())
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
                    settings.LONGEST_SLIDE_S)
    _prepared = asset
    report.note(f"slide physics on: duration {settings.LONGEST_SLIDE_S:.0f} s, slope curve flat at 1, speed curve flat at "
                f"{game_curve.values[0]:.4f}")


def _unit(asset: Any) -> float:
    """The slide speed at a speed scale of 1: the constant slide.py set, times the flat curve."""
    return max(float(asset.speed.constant) * ownership.original(CURVE_KEY).values[0], ownership.TOLERANCE)


def _new_model(now_ns: int) -> slide_model.Model:
    return slide_model.Model(now_ns, speed_order.speeds().slide, axle_slide.current(),
                             float(settings.slide_distance.value))


def _step(model: slide_model.Model, movement: Any, now_ns: int) -> float:
    return model.step(movement, now_ns, float(settings.slide_downhill_pull.value), speed_order.speeds().slide_max)


def _write_scale(movement: Any, scale: float) -> None:
    def read() -> float:
        return float(movement.MaxGroundSpeedScale.Value)

    def put(value: float) -> None:
        speed_scale = movement.MaxGroundSpeedScale
        speed_scale.Value = value
        movement.MaxGroundSpeedScale = speed_scale

    # A scale the game computed again since the last write (a skill, aiming) becomes the one to put back.
    ownership.adopt_game_value(speed_order.SCALE_KEY, ownership.TOLERANCE)
    ownership.write(speed_order.SCALE_KEY, ownership.CHARACTER, read, put, scale)


def _finish(movement: Any, now_ns: int) -> None:
    global _slide
    done, _slide = _slide, None
    speed_order.hold_scale_for_slide(False)
    try:
        ownership.restore(speed_order.SCALE_KEY)
    except Exception as exc:
        # Kept owned with the game's value, put back at the next slide's end or at stop; the slide itself is over.
        report.error_once("slide_physics:scale", f"the speed scale could not be put back after a slide: {exc!r}")
    slope = done.slope_sum / done.ground_frames if done.ground_frames else 0.0
    ratio = f"{done.ratio_sum / done.ratio_frames:.2f}" if done.ratio_frames else "-"
    boost = done.boost
    report.note(f"slide physics end ms={(now_ns - done.start_ns) // 1_000_000} by={'mod' if done.ended else 'game'} "
                f"model_speed={done.speed:.0f} game_speed={game.horizontal_speed(movement):.0f} "
                f"game_to_model={ratio} top={done.top:.0f} slope_avg={slope:+.2f} "
                f"axle={boost.speed:.2f}/{boost.flat:.2f}/{boost.slope:.2f}")


def update(character: Any, now_ns: int) -> None:
    global _slide, _armed
    asset = slide.find_asset()
    if asset is None:
        return
    movement = character.CharacterMovement
    sliding = game.is_sliding(movement)
    if not _armed:
        if sliding:
            # Begun before the model ran, such as with Slides switched off and on mid-slide: started now, the model
            # would take it back to the full slide speed. It keeps the game's own timer and curve until it ends.
            return
        _armed = True
    if _prepared is not asset:
        _prepare(asset)
    if not sliding:
        if _slide is not None:
            _finish(movement, now_ns)
        return
    if _slide is None:
        _slide = _new_model(now_ns)
        speed_order.hold_scale_for_slide(True)
    speed = _step(_slide, movement, now_ns)
    if _slide.out_of_speed() and not _slide.ended:
        _slide.ended = True
        character.SetWantsToSlide(False)
    _write_scale(movement, speed / _unit(asset))


def for_guest(guest: Any) -> dict[str, Any]:
    """On a co-op host, the scale that slows a sliding guest down as the guest's own game does; nothing otherwise, and
    the guest gets the game's scale back. The guest ends its slide itself when out of speed.

    Known limit: the host first sees the slide a little after the guest, so its model runs that much later (not
    measured; under a frame on one machine)."""
    asset = game.slide_asset()
    movement = guest.character.CharacterMovement
    if asset is None or _prepared is not asset or not game.is_sliding(movement):
        guest.memo.pop(GUEST_MEMO, None)
        return {}
    model = guest.memo.get(GUEST_MEMO)
    if model is None:
        model = guest.memo[GUEST_MEMO] = _new_model(guest.now_ns)
    return {GUEST_FIELD: _step(model, movement, guest.now_ns) / _unit(asset)}


def stop(character: Any) -> None:
    owned = ownership.is_owned(CURVE_KEY)
    holding = _slide is not None
    reset()
    keys = [CURVE_KEY, SLOPE_CURVE_KEY, DURATION_KEY] + ([speed_order.SCALE_KEY] if holding else [])
    failures = ownership.restore_each(keys)
    if failures:
        # Raised once every key was tried: the frame loop reports it, and ownership keeps what is not back yet.
        raise RuntimeError("; ".join(failures))
    if owned:
        report.note("slide physics off, game slide timer and curves restored")
