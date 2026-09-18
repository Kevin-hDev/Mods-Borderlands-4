"""Momentum slides: every slide, landing slides included, starts in the direction the player moves, not where they aim.

Verified in game on 2026-09-16 (session 3): with Move_Slide.LaunchDirection.RelativeDirection set to ParentVelocity2D,
nine landing slides left in the jump's direction within 1 degree, camera turned up to 180 degrees in the air.
"""

from typing import Any

from . import game, ownership, report, slide

DIRECTION_KEY = "Move_Slide.LaunchDirection.RelativeDirection"
MOMENTUM = "ParentVelocity2D"


def reset() -> None:
    pass


def _read() -> Any:
    return game.slide_asset().LaunchDirection.RelativeDirection


def _put(value: Any) -> None:
    asset = game.slide_asset()
    launch = asset.LaunchDirection
    launch.RelativeDirection = value
    # Assigned back whole: the SDK may hand out a copy of the struct, and a field written on a copy changes nothing.
    asset.LaunchDirection = launch


def update(character: Any, now_ns: int) -> None:
    if slide.find_asset() is None:
        return
    current = _read()
    if current.name == MOMENTUM:
        return
    ownership.write(DIRECTION_KEY, ownership.ASSET, _read, _put, type(current)[MOMENTUM])
    report.note(f"slide direction {MOMENTUM} (was {current.name})")


def stop(character: Any) -> None:
    if ownership.is_owned(DIRECTION_KEY):
        ownership.restore(DIRECTION_KEY)
        report.note("slide direction restored")
