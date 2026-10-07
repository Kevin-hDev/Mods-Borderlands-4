"""Omni Sprint's settings: the FOV option Kevin asked for on 2026-09-23, off by default.

The FOV has its own switch: without it the mod would replace the FOV chosen in the game's menu for every player,
and that menu setting would stop doing anything. The slider uses the shared camera runtime's bounds and default.
"""

import math
from . import report

from mods_base import BoolOption, SliderOption

# panel_model checks a new shortcut with normalize_keyboard_key from here.
try:
    from .apex_camera_runtime.ads_options import AdsOptions
    from .apex_camera_runtime.framing_options import FramingOptions
    from .apex_camera_runtime.loot_options import LootOptions
    from .apex_camera_runtime.speed_fov_options import SpeedFovOptions
    from .apex_camera_runtime.dynamic_options import DynamicOptions
    from .apex_camera_runtime.free_look_options import FreeLookOptions
    from .apex_camera_runtime.orbit_zoom_options import OrbitZoomOptions
    from .apex_camera_runtime.camera_distance_options import CameraDistanceOptions
    from .apex_camera_runtime.camera_option import BaseViewOption, CameraBoolOption
    from .apex_camera_runtime.camera_commands import CameraCommands
    from .apex_camera_runtime.shoulder_transition_options import ShoulderTransitionOptions
    from .apex_camera_runtime.shoulder_page import SHOULDER_PAGE
    from .apex_camera_runtime.constants import FOV_DEFAULT, FOV_MAX, FOV_MIN
    from .apex_camera_runtime.key_option import normalize_keyboard_key
    from .apex_camera_runtime import option_texts
except ModuleNotFoundError as error:
    if error.name != f"{__package__}.apex_camera_runtime":
        raise
    from apex_camera_runtime.ads_options import AdsOptions
    from apex_camera_runtime.framing_options import FramingOptions
    from apex_camera_runtime.loot_options import LootOptions
    from apex_camera_runtime.speed_fov_options import SpeedFovOptions
    from apex_camera_runtime.dynamic_options import DynamicOptions
    from apex_camera_runtime.free_look_options import FreeLookOptions
    from apex_camera_runtime.orbit_zoom_options import OrbitZoomOptions
    from apex_camera_runtime.camera_distance_options import CameraDistanceOptions
    from apex_camera_runtime.camera_option import BaseViewOption, CameraBoolOption
    from apex_camera_runtime.camera_commands import CameraCommands
    from apex_camera_runtime.shoulder_transition_options import ShoulderTransitionOptions
    from apex_camera_runtime.shoulder_page import SHOULDER_PAGE
    from apex_camera_runtime.constants import FOV_DEFAULT, FOV_MAX, FOV_MIN
    from apex_camera_runtime.key_option import normalize_keyboard_key
    from apex_camera_runtime import option_texts

# Its own switch, so a player can keep the camera without the sprint: the mod's ENABLED button turns off both
# (Kevin, 2026-09-25).
omni_sprint = BoolOption(
    "omni_sprint", True,
    display_name="Sprint in All Directions",
    description="Also sprint sideways and backward.",
)
loot = LootOptions()
speed_fov = SpeedFovOptions()
dynamic = DynamicOptions()
loot_distance = loot.distance
zoom = OrbitZoomOptions()
distance = CameraDistanceOptions()
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
    "shoulder_left", False,
    route=_set_shoulder_from_menu, ready=_camera_ready, **option_texts.SHOULDER,
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
    "orbit", False,
    route=_set_orbit_from_menu, ready=_camera_ready, cancel=_cancel_orbit_from_menu, **option_texts.ORBIT,
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
(third_person_bind, third_person_controller_bind, shoulder_bind, shoulder_controller_bind,
 orbit_bind, orbit_controller_bind) = commands.binds[:6]
(third_person_key, third_person_controller, shoulder_key, shoulder_controller,
 orbit_key, orbit_controller) = commands.options[:6]

custom_fov = BoolOption("custom_fov", False, **option_texts.CUSTOM_FOV)
fov = SliderOption("fov", FOV_DEFAULT, FOV_MIN, FOV_MAX, step=1, is_integer=True, **option_texts.FOV)
# Keep the user's actual game choice across a title-screen transition. Zero means
# no choice has been captured yet; neither value is shown as a gameplay setting.
native_fov = SliderOption("native_fov", 0, 0, 180, step=1, is_integer=False, is_hidden=True)
applied_fov = SliderOption("applied_fov", 0, 0, 180, step=1, is_integer=False, is_hidden=True)
OPTIONS = [omni_sprint, third_person, third_person_ads, third_person_key, third_person_controller,
           shoulder_left, *shoulder_transition.options, shoulder_key, shoulder_controller,
           orbit, orbit_key, orbit_controller, *commands.options[6:], *distance.options, *free_look.options, custom_fov, fov, *loot.options, *speed_fov.options, *dynamic.options, native_fov, applied_fov,
           zoom.option, distance.option, *framing.options]


def sprint_enabled() -> bool:
    """Only an explicit off turns the sprint off: it is what the mod is installed for."""
    return omni_sprint.value is not False


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
