"""The OPTIONS page's 16:10 resolution row (decision 148): off at first; on, the game in its Fullscreen at the 16:10
resolution of the screen's height, stretched over a 16:9 screen.

Kevin, 19 October 2026: the game's list has no 16:10 resolution; 2304x1440 on his 1440p screen « et pareil pour ma
1080p », the image « étirée plein écran ». Trial 112 found the stretch only in the game's Fullscreen
(resolution_game.py). Only the screen's own height: at 1728x1080 on his 1440p screen the menus took clicks in the
wrong place behind a black band (trial 113), while 2304x1440 kept them right (trial 114). A screen narrower than 16:10
(4:3, 5:4) is left as it is: its 16:10 would be wider than the screen. The player's own resolution and display mode are
kept in a hidden setting the first time the 16:10 one is applied, so that Off, or the mod disabled, gives them back
even after a relaunch; they are kept only while the mod holds the screen. The game's settings are never saved
(resolution_game.py): at each launch the mod applies the row again.
"""

import re
from typing import Any

from . import options, report, resolution_game as game

OWN = re.compile(r"(\d{3,4})x(\d{3,4}):([0-2])")
RATIO = 1.6


def sixteen_ten(screen: tuple[int, int]) -> tuple[int, int] | None:
    """16:10 at the screen's height, its width even as resolutions are; None when wider than the screen."""
    width, height = screen
    stretched = int(round(height * RATIO / 2.0)) * 2
    return (stretched, height) if stretched <= width else None


def _own() -> tuple[int, int, int] | None:
    found = OWN.fullmatch(str(options.resolution_own.value))
    return (int(found[1]), int(found[2]), int(found[3])) if found else None


def apply(on: Any) -> str:
    """The screen set for the row on or off; what happened, never raising."""
    try:
        return _apply(on is True)
    except Exception as error:
        report.error_once(f"resolution:{type(error).__name__}",
                          f"16:10 resolution unchanged: {type(error).__name__}: {str(error)[:120]}")
        return "failed"


def _apply(on: bool) -> str:
    settings = game.user()
    if not on:
        own = _own()
        if own is None:
            return "nothing_held"
        report.note("resolution_giving_back", own=list(own))
        game.apply(settings, *own)
        options.resolution_own.value = ""
        return "given_back"
    screen = game.screen(settings)
    size = sixteen_ten(screen)
    if size is None:
        report.note("resolution_screen_narrow", screen=list(screen))
        return "screen_narrow"
    if _own() is None:
        width, height, mode = game.current(settings)
        options.resolution_own.value = f"{width}x{height}:{mode}"
    report.note("resolution_applying", size=list(size), own=options.resolution_own.value)
    game.apply(settings, *size, game.FULLSCREEN)
    return "applied"


def changed(_option: Any, value: Any) -> None:
    """The row switched in the window (mods_base calls this while the mod is enabled)."""
    apply(value)


def start() -> None:
    """The mod enabled, at launch too: the row applied again, the game's own settings being unsaved; with the row off,
    a resolution of the player's still kept (a game closed by a crash) is given back."""
    apply(options.resolution.value)


def stop() -> None:
    """The mod disabled: the player's own resolution and display mode back."""
    apply(False)
