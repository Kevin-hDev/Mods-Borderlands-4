"""Full Apex Movement pack adapter to the process-wide camera runtime."""

from typing import Any

from mods_base import get_pc

try:
    from .apex_camera_runtime.option_texts import ADS_NOTICES
    from .apex_camera_runtime.bootstrap import ensure
    from .apex_camera_runtime.constants import PROTOCOL
    from .apex_camera_runtime.shared import elected, shared
except ModuleNotFoundError as error:
    # Source tests use the canonical sibling source; packaged builds carry it below the mod's only SDK root.
    if error.name != f"{__package__}.apex_camera_runtime":
        raise
    from apex_camera_runtime.option_texts import ADS_NOTICES
    from apex_camera_runtime.bootstrap import ensure
    from apex_camera_runtime.constants import PROTOCOL
    from apex_camera_runtime.shared import elected, shared

from . import camera_settings, pack, report

OWNER = "apex_movement"
PRIORITY = 200
_runtime: Any = None
_registered = False


class Settings:
    third_person_ads = staticmethod(camera_settings.ads.enabled)
    orbit_distance = staticmethod(camera_settings.zoom.distance)
    set_orbit_distance = staticmethod(camera_settings.zoom.save)
    loot_distance = staticmethod(camera_settings.loot_distance)
    fov_enabled = staticmethod(camera_settings.custom_fov_enabled)
    fov_value = staticmethod(camera_settings.fov_value)
    saved_fov_pair = staticmethod(camera_settings.saved_fov_pair)
    remember_fov_pair = staticmethod(camera_settings.remember_fov_pair)
    third_person_enabled = staticmethod(camera_settings.third_person_enabled)
    set_third_person = staticmethod(camera_settings.set_third_person)
    shoulder_left = staticmethod(camera_settings.shoulder_left_enabled)
    set_shoulder_left = staticmethod(camera_settings.set_shoulder_left)
    orbit_enabled = staticmethod(camera_settings.orbit_enabled)
    set_orbit = staticmethod(camera_settings.set_orbit)
    reject_orbit = staticmethod(camera_settings.reject_orbit)
    note = staticmethod(report.note)


ADAPTER = Settings()


def start() -> None:
    global _runtime, _registered
    if _registered or not pack.is_full():
        return
    _runtime = shared()
    _runtime.register(OWNER, PRIORITY, ADAPTER, PROTOCOL)
    _registered = True


def on_frame(now_ns: int) -> None:
    if not pack.is_full():
        return
    if not _registered:
        start()
    setup_error = _runtime.prepare_third_person(
        OWNER, camera_settings.third_person_enabled(), ensure)
    _runtime.tick(get_pc(possibly_loading=True), now_ns)
    if setup_error is not None:
        raise setup_error


def toggle_third_person() -> bool:
    return bool(_registered and _runtime.toggle_third_person(OWNER))


def toggle_shoulder() -> bool:
    return bool(_registered and _runtime.toggle_shoulder(OWNER))


def set_shoulder(left: bool) -> bool:
    return bool(_registered and _runtime.set_shoulder(OWNER, left))


def toggle_orbit() -> bool:
    return bool(_registered and _runtime.toggle_orbit(OWNER))


def set_orbit(enabled: bool) -> bool:
    return bool(_registered and _runtime.set_orbit(OWNER, enabled))


def cancel_orbit() -> bool:
    return bool(_registered and _runtime.cancel_orbit(OWNER))


def ready() -> bool:
    return bool(_registered and _runtime.camera_ready(OWNER))


def adjust_orbit_zoom(direction: int) -> bool:
    return bool(_registered and _runtime.adjust_orbit_zoom(OWNER, direction))


def aim_status() -> tuple[str, str] | None:
    reason = _runtime.ads_status(OWNER) if _registered else None
    return (reason, ADS_NOTICES[reason]) if reason is not None else None


def elected_elsewhere() -> bool:
    owner = elected()
    return owner is not None and owner != OWNER


def stop() -> None:
    global _registered
    if not _registered:
        return
    try:
        _runtime.unregister(OWNER)
    finally:
        _registered = False
