"""Omni Sprint's settings: the FOV option Kevin asked for on 2026-09-23, off by default.

The FOV has its own switch: without it the mod would replace the FOV chosen in the game's menu for every player,
and that menu setting would stop doing anything. The slider starts at 70, where the game's own starts.
"""

import math

from mods_base import BoolOption, SliderOption

GAME_MENU_MAX_FOV = 110

custom_fov = BoolOption(
    "custom_fov", False,
    display_name="Custom FOV",
    description="Use the FOV below instead of the game's.",
)
fov = SliderOption(
    "fov", 110, 70, 150, step=1, is_integer=True,
    display_name="FOV",
    description="Field of view, up to 150.",
)
# Keep the user's actual game choice across a title-screen transition. Zero means
# no choice has been captured yet; neither value is shown as a gameplay setting.
native_fov = SliderOption("native_fov", 0, 0, 180, step=1, is_integer=False, is_hidden=True)
applied_fov = SliderOption("applied_fov", 0, 0, 180, step=1, is_integer=False, is_hidden=True)
OPTIONS = [custom_fov, fov, native_fov, applied_fov]


def custom_fov_enabled() -> bool:
    """A malformed saved value must never turn the camera option on."""
    return custom_fov.value is True


def fov_value() -> float:
    """The slider's value within its bounds: the console menu takes a typed value past them (2026-09-19)."""
    value = fov.value
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        value = fov.default_value
    return float(min(fov.max_value, max(fov.min_value, value)))


def saved_fov_pair() -> tuple[float | None, float | None]:
    """Reject malformed or incomplete recovery data instead of guessing a game FOV."""
    values = (native_fov.value, applied_fov.value)
    if any(isinstance(value, bool) or not isinstance(value, (int, float))
           or not math.isfinite(value) or not 1 <= value <= 180 for value in values):
        return None, None
    return float(values[0]), float(values[1])


def remember_fov_pair(game_value: float, mod_value: float) -> None:
    """Save the restore value before the shared game field is changed."""
    if any(not math.isfinite(value) or not 1 <= value <= 180 for value in (game_value, mod_value)):
        raise ValueError("invalid FOV recovery value")
    old_values = native_fov.value, applied_fov.value
    native_fov.value, applied_fov.value = game_value, mod_value
    try:
        native_fov.mod.save_settings()
    except Exception:
        native_fov.value, applied_fov.value = old_values
        raise
