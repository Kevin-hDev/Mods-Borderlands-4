"""Axle slide: an optional boosted slide, as Axle's slides in Apex Legends, switched off by default.

Kevin, 2026-09-17: steering a slide belongs to this mode only, and each Axle slide gets a boost: faster, much further
on flat ground, and about 25 % further and faster uphill and downhill ("dans les 25 % mais pas plus"). The boosts are
measured against the normal slide, so its settings carry over. This module holds the numbers; slide_physics.py applies
them and slide_steering.py steers.
"""

from dataclasses import dataclass

from . import settings

# Flat slides read slopes of -0.06 to +0.04 and the slopes Kevin tried averaged 0.11 to 0.28 (2026-09-17, 03:09-03:13):
# the flat boost holds up to FLAT_SLOPE and has given way to the slope boost by FULL_SLOPE.
FLAT_SLOPE = 0.05
FULL_SLOPE = 0.10


@dataclass(frozen=True)
class Boost:
    speed: float
    flat: float
    slope: float


NONE = Boost(speed=1.0, flat=1.0, slope=1.0)


def current() -> Boost:
    if not settings.axle_slide.value:
        return NONE
    return Boost(speed=1.0 + float(settings.axle_speed_boost.value) / 100.0,
                 flat=1.0 + float(settings.axle_flat_distance_boost.value) / 100.0,
                 slope=1.0 + float(settings.axle_slope_boost.value) / 100.0)


def start_speed() -> float:
    return settings.speeds().slide * current().speed


def distance(boost: Boost, slope: float) -> float:
    """How many times further than a normal slide a slide goes on ground of this slope, uphill or downhill."""
    share = min(max((abs(slope) - FLAT_SLOPE) / (FULL_SLOPE - FLAT_SLOPE), 0.0), 1.0)
    return boost.flat + (boost.slope - boost.flat) * share
