"""The standalone pack's third-person shortcut and FOV settings."""

import math

from mods_base import BoolOption, SliderOption, keybind

try:
    from .apex_camera_runtime.constants import FOV_DEFAULT, FOV_MAX, FOV_MIN
    from .apex_camera_runtime.key_option import KeyboardKeybindOption
except ModuleNotFoundError as error:
    if error.name != f"{__package__}.apex_camera_runtime":
        raise
    from apex_camera_runtime.constants import FOV_DEFAULT, FOV_MAX, FOV_MIN
    from apex_camera_runtime.key_option import KeyboardKeybindOption


third_person = BoolOption(
    "third_person", False,
    display_name="Third Person",
    description="Keep the on-foot camera behind the character.",
)


def _toggle_third_person() -> None:
    from . import camera
    camera.toggle_third_person()


third_person_bind = keybind(
    "third_person_key", "P", _toggle_third_person,
    display_name="Toggle Third Person",
    description="Turn the third-person camera on or off.",
    is_hidden=True,
)
third_person_key = KeyboardKeybindOption.from_keybind(third_person_bind)
third_person_key.is_hidden = False

fov = SliderOption(
    "fov", FOV_DEFAULT, FOV_MIN, FOV_MAX, step=1, is_integer=True,
    display_name="FOV",
    description="Field of view, up to 150.",
)
native_fov = SliderOption("native_fov", 0, 0, 180, step=1, is_integer=False, is_hidden=True)
applied_fov = SliderOption("applied_fov", 0, 0, 180, step=1, is_integer=False, is_hidden=True)
OPTIONS = [third_person, third_person_key, fov, native_fov, applied_fov]


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
    # In this standalone pack, the FOV slider is authoritative while the mod is enabled.
    return True


def fov_value() -> float:
    value = fov.value
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        value = fov.default_value
    return float(min(fov.max_value, max(fov.min_value, value)))


def saved_fov_pair() -> tuple[float | None, float | None]:
    values = (native_fov.value, applied_fov.value)
    if any(isinstance(value, bool) or not isinstance(value, (int, float))
           or not math.isfinite(value) or not 1 <= value <= 180 for value in values):
        return None, None
    return float(values[0]), float(values[1])


def remember_fov_pair(game_value: float, mod_value: float) -> None:
    if any(not math.isfinite(value) or not 1 <= value <= 180 for value in (game_value, mod_value)):
        raise ValueError("invalid FOV recovery value")
    old_values = native_fov.value, applied_fov.value
    native_fov.value, applied_fov.value = game_value, mod_value
    try:
        native_fov.mod.save_settings()
    except Exception:
        native_fov.value, applied_fov.value = old_values
        raise
