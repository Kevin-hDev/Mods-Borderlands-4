"""The standalone pack's third-person shortcut and FOV settings."""

import math

from mods_base import BoolOption, SliderOption

try:
    from .apex_camera_runtime.ads_options import AdsOptions
    from .apex_camera_runtime.loot_options import LootOptions
    from .apex_camera_runtime.orbit_zoom_options import OrbitZoomOptions
    from .apex_camera_runtime.camera_option import CameraBoolOption
    from .apex_camera_runtime.camera_commands import CameraCommands
    from .apex_camera_runtime.constants import FOV_DEFAULT, FOV_MAX, FOV_MIN
    from .apex_camera_runtime import option_texts
except ModuleNotFoundError as error:
    if error.name != f"{__package__}.apex_camera_runtime":
        raise
    from apex_camera_runtime.ads_options import AdsOptions
    from apex_camera_runtime.loot_options import LootOptions
    from apex_camera_runtime.orbit_zoom_options import OrbitZoomOptions
    from apex_camera_runtime.camera_option import CameraBoolOption
    from apex_camera_runtime.camera_commands import CameraCommands
    from apex_camera_runtime.constants import FOV_DEFAULT, FOV_MAX, FOV_MIN
    from apex_camera_runtime import option_texts


loot = LootOptions()
loot_distance = loot.distance
zoom = OrbitZoomOptions()
ads = AdsOptions()
third_person_ads = ads.option

third_person = BoolOption("third_person", False, **option_texts.THIRD_PERSON)


def _toggle_third_person() -> None:
    from . import camera
    camera.toggle_third_person()


def _set_shoulder_from_menu(value: bool) -> bool:
    from . import camera
    return camera.set_shoulder(value)


def _camera_ready() -> bool:
    from . import camera
    return camera.ready()


shoulder_left = CameraBoolOption(
    "shoulder_left", False,
    route=_set_shoulder_from_menu, ready=_camera_ready, **option_texts.SHOULDER,
)


def _toggle_shoulder() -> None:
    from . import camera
    camera.toggle_shoulder()


def _set_orbit_from_menu(value: bool) -> bool:
    from . import camera
    return camera.set_orbit(value)


def _cancel_orbit_from_menu() -> bool:
    from . import camera
    return camera.cancel_orbit()


orbit = CameraBoolOption(
    "orbit", False,
    route=_set_orbit_from_menu, ready=_camera_ready, cancel=_cancel_orbit_from_menu, **option_texts.ORBIT,
)


def _toggle_orbit() -> None:
    from . import camera
    camera.toggle_orbit()


def _zoom(direction: int) -> None:
    from . import camera
    camera.adjust_orbit_zoom(direction)


commands = CameraCommands(third_person=_toggle_third_person, shoulder=_toggle_shoulder, orbit=_toggle_orbit,
                          zoom_in=lambda: _zoom(-1), zoom_out=lambda: _zoom(1))
(third_person_bind, third_person_controller_bind, shoulder_bind, shoulder_controller_bind,
 orbit_bind, orbit_controller_bind) = commands.binds[:6]
(third_person_key, third_person_controller, shoulder_key, shoulder_controller,
 orbit_key, orbit_controller) = commands.options[:6]

fov = SliderOption("fov", FOV_DEFAULT, FOV_MIN, FOV_MAX, step=1, is_integer=True, **option_texts.FOV)
native_fov = SliderOption("native_fov", 0, 0, 180, step=1, is_integer=False, is_hidden=True)
applied_fov = SliderOption("applied_fov", 0, 0, 180, step=1, is_integer=False, is_hidden=True)
OPTIONS = [third_person, third_person_ads, third_person_key, third_person_controller,
           shoulder_left, shoulder_key, shoulder_controller,
           orbit, orbit_key, orbit_controller, *commands.options[6:], fov, *loot.options, native_fov, applied_fov,
           zoom.option]


def third_person_enabled() -> bool:
    return third_person.value is True


def set_third_person(value: bool) -> None:
    _set_bool(third_person, value, "third-person")


def _set_bool(option: BoolOption, value: bool, label: str) -> None:
    if type(value) is not bool:
        raise ValueError(f"invalid {label} setting")
    previous = option.value
    commit = getattr(option, "commit", lambda item: setattr(option, "value", item))
    commit(value)
    try:
        option.mod.save_settings()
    except Exception:
        commit(previous)
        raise


def shoulder_left_enabled() -> bool:
    return shoulder_left.value is True


def set_shoulder_left(value: bool) -> None:
    _set_bool(shoulder_left, value, "shoulder")


def orbit_enabled() -> bool:
    return orbit.value is True


def set_orbit(value: bool) -> None:
    _set_bool(orbit, value, "orbit")


def reject_orbit() -> None:
    orbit.reject()


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
