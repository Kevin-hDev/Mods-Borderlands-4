"""Omni Sprint's settings: the FOV option Kevin asked for on 2026-09-23, off by default.

The FOV has its own switch: without it the mod would replace the FOV chosen in the game's menu for every player,
and that menu setting would stop doing anything. The slider uses the shared camera runtime's bounds and default.
"""

import math

from mods_base import BoolOption, SliderOption, keybind

# panel_model checks a new shortcut with normalize_keyboard_key from here.
try:
    from .apex_camera_runtime.constants import FOV_DEFAULT, FOV_MAX, FOV_MIN
    from .apex_camera_runtime.key_option import KeyboardKeybindOption, normalize_keyboard_key
except ModuleNotFoundError as error:
    if error.name != f"{__package__}.apex_camera_runtime":
        raise
    from apex_camera_runtime.constants import FOV_DEFAULT, FOV_MAX, FOV_MIN
    from apex_camera_runtime.key_option import KeyboardKeybindOption, normalize_keyboard_key

# Its own switch, so a player can keep the camera without the sprint: the mod's ENABLED button turns off both
# (Kevin, 2026-09-25).
omni_sprint = BoolOption(
    "omni_sprint", True,
    display_name="Sprint in All Directions",
    description="Also sprint sideways and backward.",
)
third_person = BoolOption(
    "third_person", False,
    display_name="Third Person",
    description="Keep the on-foot camera behind the character.",
)


def _toggle_third_person() -> None:
    # Imported on press to keep settings as the camera adapter's dependency, never the reverse.
    from . import camera
    camera.toggle_third_person()


third_person_bind = keybind(
    "third_person_key", "P", _toggle_third_person,
    display_name="Toggle Third Person",
    description="Turn the third-person camera on or off.",
    is_hidden=True,
)
third_person_key = KeyboardKeybindOption.sole_entry(third_person_bind)

custom_fov = BoolOption(
    "custom_fov", False,
    display_name="Custom FOV",
    description="Use the FOV below instead of the game's.",
)
fov = SliderOption(
    "fov", FOV_DEFAULT, FOV_MIN, FOV_MAX, step=1, is_integer=True,
    display_name="FOV",
    description="Field of view, up to 150.",
)
# Keep the user's actual game choice across a title-screen transition. Zero means
# no choice has been captured yet; neither value is shown as a gameplay setting.
native_fov = SliderOption("native_fov", 0, 0, 180, step=1, is_integer=False, is_hidden=True)
applied_fov = SliderOption("applied_fov", 0, 0, 180, step=1, is_integer=False, is_hidden=True)
OPTIONS = [omni_sprint, third_person, third_person_key, custom_fov, fov, native_fov, applied_fov]


def sprint_enabled() -> bool:
    """Only an explicit off turns the sprint off: it is what the mod is installed for."""
    return omni_sprint.value is not False


def third_person_enabled() -> bool:
    return third_person.value is True


def set_third_person(value: bool) -> None:
    if type(value) is not bool:
        raise ValueError("invalid third-person setting")
    previous = third_person.value
    third_person.value = value
    try:
        third_person.mod.save_settings()
    except Exception:
        third_person.value = previous
        raise


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
