"""Camera options owned by the full Apex Movement pack."""

import math
from . import report

from mods_base import BoolOption, SliderOption

try:
    from .apex_camera_runtime.ads_options import AdsOptions
    from .apex_camera_runtime.framing_options import FramingOptions
    from .apex_camera_runtime.loot_options import LootOptions
    from .apex_camera_runtime.speed_fov_options import SpeedFovOptions
    from .apex_camera_runtime.dynamic_options import DynamicOptions
    from .apex_camera_runtime.omni_direction_options import SLIDE, OmniDirectionOptions
    from .apex_camera_runtime.free_look_options import FreeLookOptions
    from .apex_camera_runtime.orbit_zoom_options import OrbitZoomOptions
    from .apex_camera_runtime.camera_distance_options import CameraDistanceOptions
    from .apex_camera_runtime.look_sensitivity_options import LookSensitivityOptions
    from .apex_camera_runtime.weapon_optic_options import WeaponOpticOptions
    from .apex_camera_runtime.camera_option import BaseViewOption, CameraBoolOption
    from .apex_camera_runtime.camera_commands import CameraCommands
    from .apex_camera_runtime.shoulder_transition_options import ShoulderTransitionOptions
    from .apex_camera_runtime.shoulder_page import SHOULDER_PAGE
    from .apex_camera_runtime.constants import FOV_DEFAULT, FOV_MAX, FOV_MIN
    from .apex_camera_runtime import option_texts
except ModuleNotFoundError as error:
    if error.name != f"{__package__}.apex_camera_runtime":
        raise
    from apex_camera_runtime.ads_options import AdsOptions
    from apex_camera_runtime.framing_options import FramingOptions
    from apex_camera_runtime.loot_options import LootOptions
    from apex_camera_runtime.speed_fov_options import SpeedFovOptions
    from apex_camera_runtime.dynamic_options import DynamicOptions
    from apex_camera_runtime.omni_direction_options import SLIDE, OmniDirectionOptions
    from apex_camera_runtime.free_look_options import FreeLookOptions
    from apex_camera_runtime.orbit_zoom_options import OrbitZoomOptions
    from apex_camera_runtime.camera_distance_options import CameraDistanceOptions
    from apex_camera_runtime.look_sensitivity_options import LookSensitivityOptions
    from apex_camera_runtime.weapon_optic_options import WeaponOpticOptions
    from apex_camera_runtime.camera_option import BaseViewOption, CameraBoolOption
    from apex_camera_runtime.camera_commands import CameraCommands
    from apex_camera_runtime.shoulder_transition_options import ShoulderTransitionOptions
    from apex_camera_runtime.shoulder_page import SHOULDER_PAGE
    from apex_camera_runtime.constants import FOV_DEFAULT, FOV_MAX, FOV_MIN
    from apex_camera_runtime import option_texts

loot = LootOptions()
speed_fov = SpeedFovOptions()
dynamic = DynamicOptions()
# Apex Movement keeps the slide on the sides and backward: a move of its own (Kevin, 2026-10-09).
omni = OmniDirectionOptions(SLIDE)
loot_distance = loot.distance
zoom = OrbitZoomOptions()
distance = CameraDistanceOptions()
sensitivity = LookSensitivityOptions()
ads = AdsOptions()
framing = FramingOptions(note=report.note)
shoulder_transition = ShoulderTransitionOptions()
third_person_ads = ads.option

def _base_view_locked() -> bool:
    from . import camera
    return camera.base_view_locked()


third_person = BaseViewOption("third_person", False, locked=_base_view_locked, **option_texts.THIRD_PERSON)


def _toggle_third_person() -> None:
    # Imported on press to keep settings as the camera adapter's dependency, never the reverse.
    from . import camera
    camera.toggle_third_person()


def _set_shoulder_from_menu(value: bool) -> bool:
    from . import camera
    return camera.set_shoulder(value)


def _camera_ready() -> bool:
    from . import camera
    return camera.ready()


shoulder_left = CameraBoolOption(
    "shoulder_left", False, **option_texts.SHOULDER,
    route=_set_shoulder_from_menu, ready=_camera_ready,
)


def _toggle_shoulder() -> None:
    from . import camera
    camera.toggle_shoulder()


def _set_orbit_from_menu(value: bool) -> bool:
    from . import camera
    return camera.set_orbit(value)


def _cancel_orbit_from_menu(*, restore: bool = True) -> bool:
    from . import camera
    return camera.cancel_orbit(restore=restore)


orbit = CameraBoolOption(
    "orbit", False, **option_texts.ORBIT,
    route=_set_orbit_from_menu, ready=_camera_ready, cancel=_cancel_orbit_from_menu,
)


def _toggle_orbit() -> None:
    from . import camera
    camera.toggle_orbit()


def _zoom(direction: int) -> None:
    from . import camera
    camera.adjust_orbit_zoom(direction)


def _cycle_distance() -> None:
    from . import camera
    camera.cycle_camera_distance()


commands = CameraCommands(third_person=_toggle_third_person, shoulder=_toggle_shoulder, orbit=_toggle_orbit,
                          zoom_in=lambda: _zoom(-1), zoom_out=lambda: _zoom(1), camera_distance=_cycle_distance)
free_look = FreeLookOptions(commands)
optics = WeaponOpticOptions(commands)
(third_person_bind, third_person_controller_bind, shoulder_bind, shoulder_controller_bind,
 orbit_bind, orbit_controller_bind) = commands.binds[:6]
(third_person_key, third_person_controller, shoulder_key, shoulder_controller,
 orbit_key, orbit_controller) = commands.options[:6]
custom_fov = BoolOption("custom_fov", False, **option_texts.CUSTOM_FOV)
fov = SliderOption(
    "fov", FOV_DEFAULT, FOV_MIN, FOV_MAX, step=1, is_integer=True, **option_texts.FOV,
)
native_fov = SliderOption("native_fov", 0, 0, 180, step=1, is_integer=False, is_hidden=True)
applied_fov = SliderOption("applied_fov", 0, 0, 180, step=1, is_integer=False, is_hidden=True)
# The custom panel exposes only player choices; recovery values stay private.
# The field of view right after the view, as on the other camera mods' CAMERA VIEW page (Kevin, 2026-10-07); the
# shoulder's settings show on their own SHOULDER VIEW tab (SHOULDER_PAGE).
VISIBLE = (third_person, third_person_ads, *optics.options, custom_fov, fov, *distance.options, shoulder_left, *shoulder_transition.options,
           *free_look.options, orbit, *loot.options, *sensitivity.options, *omni.options)
# The settings each one-card tab shows (panel_options.CARD_PAGES), kept off the CAMERA VIEW tab.
CARD_SETTINGS = {"shoulder": SHOULDER_PAGE, "aiming": (third_person_ads.identifier,
                                                       *(option.identifier for option in optics.options)),
                 "sensitivity": tuple(option.identifier for option in sensitivity.options),
                 "omni_direction": tuple(option.identifier for option in omni.options)}
# The DYNAMIC CAMERA tab's settings, apart from the CAMERA tab's.
DYNAMIC = (*speed_fov.options, *dynamic.options)
ALL = [third_person, third_person_ads, third_person_key, third_person_controller,
       shoulder_left, *shoulder_transition.options, shoulder_key, shoulder_controller,
       orbit, orbit_key, orbit_controller, *commands.options[6:], *distance.options, *free_look.options, custom_fov, fov, *loot.options, *speed_fov.options, *dynamic.options, *omni.options, *sensitivity.options, *optics.options, native_fov, applied_fov,
           zoom.option, distance.option, *framing.options]


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
    return custom_fov.value is True


def fov_value() -> float:
    value = fov.value
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        value = fov.default_value
    return float(min(fov.max_value, max(fov.min_value, value)))


def saved_fov_pair() -> tuple[float | None, float | None]:
    values = native_fov.value, applied_fov.value
    if any(isinstance(value, bool) or not isinstance(value, (int, float))
           or not math.isfinite(value) or not 1 <= value <= 180 for value in values):
        return None, None
    return float(values[0]), float(values[1])


def remember_fov_pair(native: float, applied: float) -> None:
    if any(not math.isfinite(value) or not 1 <= value <= 180 for value in (native, applied)):
        raise ValueError("invalid FOV recovery value")
    previous = native_fov.value, applied_fov.value
    native_fov.value, applied_fov.value = native, applied
    try:
        native_fov.mod.save_settings()
    except Exception:
        native_fov.value, applied_fov.value = previous
        raise
