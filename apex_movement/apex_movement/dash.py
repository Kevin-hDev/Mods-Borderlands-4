"""Longer dash: the dash goes further at the game's own speed, it does not go faster.

Move_Dash's speed curve (read on 2026-09-16) keeps full speed until 0.15 s, drops to 0.18 at 0.17 s, then comes back
up to 0.48 at 0.33 s. Stretching the whole curve in time (0.5.0) gave the distance (508 -> 671-683 at 130 %, measured
on 2026-09-17) but also stretched the drop and the pick-up after it: Kevin saw the dash move twice, "comme une espèce
de rebond", and did not feel the extra distance. So only the full-speed part is lengthened now: Duration and every
curve point after that part move later by the same time, and the drop and pick-up keep the game's timing. At full
speed, extra distance is speed x time: a dash f times the game's 508 needs (f - 1) x 508 / speed more seconds.

Past 300 % the dash lasts no longer: through a longer dash the game's dash animation played again and again (Kevin,
2026-09-19, at 1000 %: "l'animation de l'ancien qui s'enchaîne"; fine at 300 %). It keeps 300 %'s timing and starts
faster instead, then slows down in a straight line to the game's speed and ends as the game's dash ends (Kevin: "la
poussée du début doit être puissante mais il doit y avoir une perte de vitesse du début à l'arrivée, ça doit rester
une propulsion").

That push lives in the speed curve alone, and speed.constant keeps the game's value. Loveless's dash,
Move_Dash_Robodealer, follows its curve and its duration but not speed.constant: with 15282 written there, it ran
2465 -> 407 -> 76 -> 196, the curve Apex wrote times the game's 2500, frame for frame (2026-09-21). Move_Dash
multiplies the two, so the same curve gives the first four the same dash as before.
"""

from dataclasses import dataclass, replace
from typing import Any

from unrealsdk.unreal import WeakPointer

from . import dash_lookup, game, ownership, report, settings

# The key of the dash the first four characters share; every other dash is owned under its own name, so each one
# gets its own values back — one key for two dashes would put one's values into the other.
SHAPE_KEY = "Move_Dash.shape"
# A few characters, a few dashes: the bound only guards against a surprise.
MAX_DASHES = 8
# The game's dash on flat ground, measured on 2026-09-17 (00:59): the base the distance percentage applies to.
GAME_DISTANCE = 508.0
# The longest dash, in game dashes, that still plays the game's animation once (Kevin, 2026-09-19).
LONGEST = 3.0


@dataclass(frozen=True)
class Shape:
    """Everything the mod writes in Move_Dash: its duration, its speed, and every point of its speed curve."""

    duration: float
    speed: float
    # One entry per curve point, in the curve's order.
    times: tuple[float, ...]
    values: tuple[float, ...]
    arrive: tuple[float, ...]
    leave: tuple[float, ...]


_written: set[str] = set()


def reset() -> None:
    """Nothing of its own to forget: the game's dash belongs to ownership, which stop gives back."""


def _key(asset: Any) -> str:
    return f"{getattr(asset, 'Name', 'Move_Dash')}.shape"


def _keys(asset: Any) -> Any:
    return asset.SpeedScaleCurve.EditorCurveData.keys


def read(asset: Any) -> Shape:
    keys = list(_keys(asset))
    return Shape(float(asset.Duration.constant), float(asset.speed.constant), tuple(float(key.time) for key in keys),
                 tuple(float(key.Value) for key in keys), tuple(float(key.ArriveTangent) for key in keys),
                 tuple(float(key.LeaveTangent) for key in keys))


def has_full_speed_start(shape: Shape) -> bool:
    """The curve starts with two points at the same value: the full-speed part that gets lengthened."""
    return len(shape.values) >= 2 and abs(shape.values[0] - shape.values[1]) <= ownership.TOLERANCE


def lengthened(shape: Shape, extra: float) -> Shape:
    """Moves Duration and every point after the first (the end of the full-speed part and all later ones) by extra."""
    return replace(shape, duration=shape.duration + extra,
                   times=tuple(time if index == 0 else time + extra for index, time in enumerate(shape.times)))


def pushed(shape: Shape, extra_distance: float) -> Shape:
    """Starts faster and slows down in a straight line, over the full-speed part, to the game's speed; the points
    after it keep the game's speeds, so the dash ends as the game's does.

    That part then averages (start + game speed) / 2 instead of the game speed, which gives the extra distance. Only
    the curve's first point rises, and the speed stays the game's: a dash that never reads its speed still reads its
    curve (see the top of this file).
    """
    main = shape.times[1] - shape.times[0]
    first = shape.values[0] * (1.0 + 2.0 * extra_distance / (main * shape.speed))
    slope = (shape.values[1] - first) / main
    return replace(shape, values=(first, *shape.values[1:]), arrive=(shape.arrive[0], slope, *shape.arrive[2:]),
                   leave=(slope, *shape.leave[1:]))


def wanted(game_shape: Shape, factor: float) -> Shape:
    per_dash = GAME_DISTANCE / max(game_shape.speed, 1.0)
    longer = lengthened(game_shape, (min(factor, LONGEST) - 1.0) * per_dash)
    if factor <= LONGEST:
        return longer
    return pushed(longer, (factor - LONGEST) * GAME_DISTANCE)


def close(a: Shape, b: Shape) -> bool:
    values_a = (a.duration, a.speed, *a.times, *a.values, *a.arrive, *a.leave)
    values_b = (b.duration, b.speed, *b.times, *b.values, *b.arrive, *b.leave)
    return len(values_a) == len(values_b) and all(abs(x - y) <= ownership.TOLERANCE for x, y in zip(values_a, values_b))


def _put(pointer: Any, shape: Shape) -> None:
    # Written into the dash this key belongs to, not whichever the character plays now.
    asset = ownership.loaded(pointer())
    # Structs assigned back whole: the SDK may hand out a copy, and a field written on a copy changes nothing.
    duration = asset.Duration
    duration.constant = shape.duration
    asset.Duration = duration
    speed = asset.speed
    speed.constant = shape.speed
    asset.speed = speed
    # Curve points are written in place through the array's views (verified in game on 2026-09-17): assigning the
    # array back onto itself is avoided, since copying an array over its own memory is not known to be safe.
    for key, time, value, arrive, leave in zip(_keys(asset), shape.times, shape.values, shape.arrive, shape.leave):
        key.time, key.Value, key.ArriveTangent, key.LeaveTangent = time, value, arrive, leave
    if not close(read(asset), shape):
        # Fatal for this movement: the frame loop switches it off and reports it, the game's dash stays as it was.
        raise RuntimeError("Move_Dash kept its old values after the write")


def update(character: Any, now_ns: int) -> None:
    dash_lookup.note(character.CharacterMovement)
    asset = game.dash_asset(now_ns)
    if asset is None:
        # A game before the Hoverpack has no dash loaded at all; two characters' dashes loaded at once wait for the
        # first one played to say which is ours.
        report.error_once("dash_asset", "no dash of this character found yet; dashes keep the game's own length "
                                        "meanwhile")
        return
    key = _key(asset)
    # The game's dash, not the one written: past 300 % the written curve no longer starts flat.
    game_shape = ownership.original(key) if ownership.is_owned(key) else read(asset)
    if not has_full_speed_start(game_shape):
        # A game update changed the curve: lengthening another part would bring the double move back.
        report.error_once("dash_curve", "Move_Dash's speed curve changed shape; dashes keep the game's own length")
        return
    factor = float(settings.dash_distance.value) / 100.0
    target = wanted(game_shape, factor)
    # Read every frame rather than remembered: the game can put Move_Dash back without a character change.
    if not close(read(asset), target):
        if key not in _written and len(_written) >= MAX_DASHES:
            return
        pointer = WeakPointer(asset)
        ownership.write(key, ownership.ASSET, lambda: read(ownership.loaded(pointer())),
                        lambda shape: _put(pointer, shape), target)
        _written.add(key)
        push = (f", starting at {target.values[0] * target.speed:.0f} "
                f"(game {game_shape.values[0] * game_shape.speed:.0f})" if factor > LONGEST else "")
        report.note(f"dash distance {factor * 100:.0f}% lasting {target.duration * 1000:.0f} ms "
                    f"(game {game_shape.duration * 1000:.0f} ms){push} on {key[:-len('.shape')]}")


def stop(character: Any) -> None:
    restored = False
    for key in sorted(_written):
        if ownership.is_owned(key):
            # Raises when a value did not come back: the frame loop reports it and tries again, _written intact.
            ownership.restore(key)
            restored = True
    _written.clear()
    if restored:
        report.note("dash distance off, game dash restored")
