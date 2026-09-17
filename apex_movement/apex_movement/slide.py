"""Fast slides: a slide starts at the set speed, boosted by the Axle slide, and a jump early in the slide keeps that speed.

Ported from Auto Sprint 1.5.0, verified in game on 2026-09-15. The start speed comes from Move_Slide's speed
constant, which applies to every slide, landing slides included. Velocity written during a slide is overwritten by the
game on the ground, but a jump launches from it (about 1.05 times the written speed): that is the slide jump.
"""

from typing import Any

from . import axle_slide, game, ownership, report

SPEED_KEY = "Move_Slide.speed.constant"
# Auto Sprint 1.5.0's window, whose feel Kevin approved: a jump later in the slide launches at the slowed slide speed.
BOOST_NS = 700_000_000

_started_ns: int | None = None
_top_speed = 0.0


def reset() -> None:
    global _started_ns
    _started_ns = None


def _put_constant(value: float) -> None:
    asset = game.slide_asset()
    speed = asset.speed
    speed.constant = value
    # Assigned back whole: the SDK may hand out a copy of the struct, and a field written on a copy changes nothing.
    asset.speed = speed


def _set_start_speed(movement: Any, target: float) -> None:
    """Called on the ground, standing, not aiming, not sliding: the speed bonus is then the one slides start with (1.15).

    Aiming lowers it to 0.92, which would give the wrong constant. Walking counts too, so a landing slide after a
    walking jump starts at the set speed even before the first sprint.
    """
    asset = game.slide_asset()
    scale = float(movement.MaxGroundSpeedScale.Value) if asset.bSpeedAffectedByMaxGroundSpeedScale else 1.0
    keys = asset.SpeedScaleCurve.EditorCurveData.keys
    curve_start = float(keys[0].Value) if len(keys) > 0 else 1.0
    divisor = scale * curve_start
    if divisor < 0.01:
        return
    # Start speed = constant x speed bonus x curve at time 0 (720 x 1.15 x 1.1017 = 912, verified in game).
    wanted = target / divisor
    if abs(float(asset.speed.constant) - wanted) <= 0.5:
        return
    ownership.write(SPEED_KEY, ownership.ASSET, lambda: float(game.slide_asset().speed.constant), _put_constant, wanted)
    report.note(f"slide start speed {target:.0f} (constant {wanted:.0f})")


def _track(movement: Any, now_ns: int, target: float) -> None:
    global _started_ns, _top_speed
    speed = game.horizontal_speed(movement)
    if not game.is_sliding(movement):
        if _started_ns is not None:
            ended = "ground" if game.is_on_ground(movement) else "air"
            report.note(f"slide end on={ended} ms={(now_ns - _started_ns) // 1_000_000} "
                        f"top_speed={_top_speed:.0f} speed_now={speed:.0f}")
        _started_ns = None
        return
    if _started_ns is None:
        _started_ns, _top_speed = now_ns, 0.0
    # Read before this frame's write: the speed the game itself gave the slide.
    _top_speed = max(_top_speed, speed)
    if now_ns - _started_ns <= BOOST_NS and speed < target - 1.0:
        game.set_horizontal_speed(movement, target)


def update(character: Any, now_ns: int) -> None:
    if game.slide_asset() is None:
        report.error_once("slide_asset", "Move_Slide not found yet; slides keep the game's own speed meanwhile")
        return
    movement = character.CharacterMovement
    target = axle_slide.start_speed()
    # Not during a slide: the game reads the constant only when a slide starts, and meanwhile the speed curve belongs to
    # slide_physics, so the constant followed it every frame (610 rewrites in three slides, 2026-09-17, 03:11-03:13).
    if (game.is_on_ground(movement) and not character.bIsCrouched and not game.is_aiming(character)
            and not game.is_sliding(movement)):
        _set_start_speed(movement, target)
    _track(movement, now_ns, target)


def stop(character: Any) -> None:
    reset()
    ownership.restore(SPEED_KEY)
