"""Longer dash: the dash goes further at the game's own speed, it does not go faster.

Move_Dash's speed curve (read on 2026-09-16) keeps full speed until 0.15 s, drops to 0.18 at 0.17 s, then comes back
up to 0.48 at 0.33 s. Stretching the whole curve in time (0.5.0) gave the distance (508 -> 671-683 at 130 %, measured
on 2026-09-17) but also stretched the drop and the pick-up after it: Kevin saw the dash move twice, "comme une espèce
de rebond", and did not feel the extra distance. So only the full-speed part is lengthened now: Duration and every
curve point after that part move later by the same time, and the drop and pick-up keep the game's timing. At full
speed, extra distance is speed x time: a dash f times the game's 508 needs (f - 1) x 508 / speed more seconds.
"""

from dataclasses import dataclass
from typing import Any

from . import game, ownership, report, settings

TIMING_KEY = "Move_Dash.timing"
# The game's dash on flat ground, measured on 2026-09-17 (00:59): the base the distance percentage applies to.
GAME_DISTANCE = 508.0
# Game floats are 32-bit: a value read back differs from the one written by less than this.
TOLERANCE = 1e-4


@dataclass(frozen=True)
class Timing:
    duration: float
    # The time of every point of the speed curve, in the curve's order.
    times: tuple[float, ...]


_applied: float | None = None


def reset() -> None:
    global _applied
    _applied = None


def _keys(asset: Any) -> Any:
    return asset.SpeedScaleCurve.EditorCurveData.keys


def read(asset: Any) -> Timing:
    return Timing(float(asset.Duration.constant), tuple(float(key.time) for key in _keys(asset)))


def has_full_speed_start(asset: Any) -> bool:
    """The curve starts with two points at the same value: the full-speed part that gets lengthened."""
    keys = list(_keys(asset))
    return len(keys) >= 2 and abs(float(keys[0].Value) - float(keys[1].Value)) <= TOLERANCE


def lengthened(timing: Timing, extra: float) -> Timing:
    """Moves Duration and every point after the first (the end of the full-speed part and all later ones) by extra."""
    return Timing(timing.duration + extra, tuple(time if index == 0 else time + extra
                                                 for index, time in enumerate(timing.times)))


def close(a: Timing, b: Timing) -> bool:
    values_a, values_b = (a.duration, *a.times), (b.duration, *b.times)
    return len(values_a) == len(values_b) and all(abs(x - y) <= TOLERANCE for x, y in zip(values_a, values_b))


def _put(timing: Timing) -> None:
    asset = game.dash_asset()
    duration = asset.Duration
    duration.constant = timing.duration
    # Assigned back whole: the SDK may hand out a copy of the struct, and a field written on a copy changes nothing.
    asset.Duration = duration
    # Curve points are written in place through the array's views (verified in game on 2026-09-17): assigning the
    # array back onto itself is avoided, since copying an array over its own memory is not known to be safe.
    for key, time in zip(_keys(asset), timing.times):
        key.time = time
    if not close(read(asset), timing):
        # Fatal for this movement: the frame loop switches it off and reports it, the game's dash stays as it was.
        raise RuntimeError("Move_Dash kept its old timing after the write")


def update(character: Any, now_ns: int) -> None:
    global _applied
    factor = float(settings.dash_distance.value) / 100.0
    if _applied == factor:
        return
    asset = game.dash_asset()
    if asset is None:
        report.error_once("dash_asset", "Move_Dash not found yet; dashes keep the game's own length meanwhile")
        return
    _applied = factor
    if not has_full_speed_start(asset):
        # A game update changed the curve: lengthening another part would bring the double move back.
        report.error_once("dash_curve", "Move_Dash's speed curve changed shape; dashes keep the game's own length")
        return
    game_timing = ownership.original(TIMING_KEY) if ownership.is_owned(TIMING_KEY) else read(asset)
    extra = (factor - 1.0) * GAME_DISTANCE / max(float(asset.speed.constant), 1.0)
    wanted = lengthened(game_timing, extra)
    if not close(read(asset), wanted):
        ownership.write(TIMING_KEY, ownership.ASSET, lambda: read(game.dash_asset()), _put, wanted)
        report.note(f"dash distance {factor * 100:.0f}% lasting {wanted.duration * 1000:.0f} ms "
                    f"(game {game_timing.duration * 1000:.0f} ms)")


def stop(character: Any) -> None:
    reset()
    if ownership.is_owned(TIMING_KEY):
        ownership.restore(TIMING_KEY)
        report.note("dash distance off, game dash restored")
