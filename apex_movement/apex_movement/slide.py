"""Fast slides: a slide starts at the set speed, boosted by the Axle slide, and a jump early in the slide keeps that speed.

Ported from Auto Sprint 1.5.0, verified in game on 2026-09-15. The start speed comes from Move_Slide's speed
constant, which applies to every slide, landing slides included. Velocity written during a slide is overwritten by the
game on the ground, but a jump launches from it (about 1.05 times the written speed): that is the slide jump.
"""

from typing import Any

from . import axle_slide, game, ownership, report, speed_order

SPEED_KEY = "Move_Slide.speed.constant"
# Auto Sprint 1.5.0's window, whose feel Kevin approved: a jump later in the slide launches at the slowed slide speed.
BOOST_NS = 700_000_000
# The real divisor is about 1.27 (1.15 x 1.1017): one this small means the speed bonus or the curve reads zero, and
# dividing by it would write a constant a hundred times too large or more.
MIN_DIVISOR = 0.01
# A slide less than this below its target is left alone: a raise that small shows in no jump, and would only add a
# velocity write every frame.
TARGET_MARGIN = 1.0
# Every module of the slides needs Move_Slide, so one line, under one key, says it is missing for all of them.
MISSING_ASSET = "Move_Slide not found yet; slides stay the game's own meanwhile"

_started_ns: int | None = None
_target = 0.0
_top_speed = 0.0
# Set by a frame without a slide: only a slide begun after it is raised.
_armed = False


def reset() -> None:
    global _started_ns, _armed
    _started_ns, _armed = None, False


def find_asset() -> Any:
    """Move_Slide, or None after reporting once, for every module of the slides, that the game has not loaded it."""
    asset = game.slide_asset()
    if asset is None:
        report.error_once("slide_asset", MISSING_ASSET)
    return asset


def _speed_constant() -> float:
    return float(ownership.loaded(game.slide_asset()).speed.constant)


def _put_constant(value: float) -> None:
    asset = ownership.loaded(game.slide_asset())
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
    # The game's scale, not the walk key's lower one: Move_Slide is shared by every character of the machine.
    scale = speed_order.game_scale(movement) if asset.bSpeedAffectedByMaxGroundSpeedScale else 1.0
    keys = asset.SpeedScaleCurve.EditorCurveData.keys
    curve_start = float(keys[0].Value) if len(keys) > 0 else 1.0
    divisor = scale * curve_start
    if divisor < MIN_DIVISOR:
        return
    # Start speed = constant x speed bonus x curve at time 0 (720 x 1.15 x 1.1017 = 912, verified in game).
    wanted = target / divisor
    if abs(float(asset.speed.constant) - wanted) <= ownership.SPEED_TOLERANCE:
        ownership.claim(SPEED_KEY, ownership.ASSET, _speed_constant, _put_constant)
        return
    ownership.write(SPEED_KEY, ownership.ASSET, _speed_constant, _put_constant, wanted)
    report.note(f"slide start speed {target:.0f} (constant {wanted:.0f})")


def _track(movement: Any, now_ns: int, target: float) -> None:
    global _started_ns, _target, _top_speed, _armed
    speed = game.horizontal_speed(movement)
    if not game.is_sliding(movement):
        _armed = True
        if _started_ns is not None:
            ended = "ground" if game.is_on_ground(movement) else "air"
            report.note(f"slide end on={ended} ms={(now_ns - _started_ns) // 1_000_000} "
                        f"top_speed={_top_speed:.0f} speed_now={speed:.0f}")
        _started_ns = None
        return
    if _started_ns is None:
        if not _armed:
            # Begun before this module ran, such as with Slides switched off and on mid-slide: raised now, the slowed
            # slide would jump back to its start speed.
            return
        # Kept for the whole slide, as slide_physics keeps its boost: an Axle slide switched on mid-slide would
        # otherwise be raised to the boosted speed while its model stays at the normal one.
        _started_ns, _target, _top_speed = now_ns, target, 0.0
    # Read before this frame's write: the speed the game itself gave the slide.
    _top_speed = max(_top_speed, speed)
    if now_ns - _started_ns <= BOOST_NS and speed < _target - TARGET_MARGIN:
        game.set_horizontal_speed(movement, _target)


def update(character: Any, now_ns: int) -> None:
    if find_asset() is None:
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
