"""Axle slide steering: while the Axle slide is on, a slide turns with the move stick faster than the game lets it.

Measured on 2026-09-17 (01:11): Move_Slide.MoveLRRate turns a slide by about that many degrees a second with the stick
fully to the side (about 205 at 220). Switched off with the Axle slide, which puts the game's 55 back: a normal slide
is not steered (Kevin, 2026-09-17). The default and its slider are in settings.py.
"""

from typing import Any

from . import game, ownership, report, settings

RATE_KEY = "Move_Slide.MoveLRRate.constant"


def reset() -> None:
    pass


def _read() -> float:
    return float(game.slide_asset().MoveLRRate.constant)


def _put(value: float) -> None:
    asset = game.slide_asset()
    rate = asset.MoveLRRate
    rate.constant = value
    # Assigned back whole: the SDK may hand out a copy of the struct, and a field written on a copy changes nothing.
    asset.MoveLRRate = rate


def update(character: Any, now_ns: int) -> None:
    if game.slide_asset() is None:
        report.error_once("slide_asset", "Move_Slide not found yet; slides keep the game's own speed meanwhile")
        return
    rate = float(settings.axle_steering.value)
    if abs(_read() - rate) <= 0.01:
        return
    ownership.write(RATE_KEY, ownership.ASSET, _read, _put, rate)
    report.note(f"axle slide steering {rate:.0f} degrees a second")


def stop(character: Any) -> None:
    if ownership.is_owned(RATE_KEY):
        ownership.restore(RATE_KEY)
        report.note("axle slide steering off, game slide steering restored")
