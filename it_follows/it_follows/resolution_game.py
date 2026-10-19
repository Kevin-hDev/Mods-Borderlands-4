"""The game's side of the 16:10 resolution (resolution.py): the engine's GameUserSettings, read and applied, never
saved.

Trial 112 (vérifié en jeu, Kevin's 2560x1440 screen): in the game's Fullscreen (EWindowMode 0, exclusive) a 2304x1440
resolution draws a 2304x1440 image, which the screen stretches with no black bars; in Windowed Fullscreen the game
ignores the resolution. SaveSettings is never called: the game's settings file keeps the player's own, so a mod
removed leaves the game as it was.
"""

from typing import Any

import unrealsdk

SETTINGS = "GameUserSettings"
# EWindowMode: 0 Fullscreen (the game's "Fullscreen", exclusive), 1 Windowed Fullscreen, 2 Windowed.
FULLSCREEN = 0
MODES = (0, 1, 2)
SMALLEST, LARGEST = 480, 8640


def user() -> Any:
    return unrealsdk.find_class(SETTINGS).ClassDefaultObject.GetGameUserSettings()


def _size(point: Any) -> tuple[int, int]:
    return int(point.X), int(point.Y)


def current(settings: Any) -> tuple[int, int, int]:
    """The resolution and display mode the game uses now."""
    width, height = _size(settings.GetScreenResolution())
    return width, height, int(settings.GetFullscreenMode())


def screen(settings: Any) -> tuple[int, int]:
    return _size(settings.GetDesktopResolution())


def valid(width: int, height: int, mode: int) -> bool:
    return mode in MODES and all(type(side) is int and SMALLEST <= side <= LARGEST for side in (width, height))


def apply(settings: Any, width: int, height: int, mode: int) -> None:
    """Applies a resolution and display mode, unsaved; raises ValueError before anything is set when they are none."""
    if not valid(width, height, mode):
        raise ValueError(f"refused {width}x{height} mode {mode}")
    settings.SetScreenResolution(unrealsdk.make_struct("IntPoint", X=width, Y=height))
    settings.SetFullscreenMode(mode)
    settings.ApplyResolutionSettings(False)
