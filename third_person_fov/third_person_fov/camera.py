"""Priority-150 adapter to the process-wide camera runtime."""

from typing import Any

from mods_base import get_pc

try:
    from .apex_camera_runtime.option_texts import ADS_NOTICES
    from .apex_camera_runtime.bootstrap import ensure
    from .apex_camera_runtime.framing_session import confirm_settings
    from .apex_camera_runtime.constants import PROTOCOL
    from .apex_camera_runtime.shared import IncompatibleState, elected, shared
except ModuleNotFoundError as error:
    if error.name != f"{__package__}.apex_camera_runtime":
        raise
    from apex_camera_runtime.option_texts import ADS_NOTICES
    from apex_camera_runtime.bootstrap import ensure
    from apex_camera_runtime.framing_session import confirm_settings
    from apex_camera_runtime.constants import PROTOCOL
    from apex_camera_runtime.shared import IncompatibleState, elected, shared

from . import report, settings

OWNER = "third_person_fov"
# Apex Movement (200) comes first, Kevin's first mod (2026-09-25); this pack stays above Omni Sprint (100).
PRIORITY = 150
_runtime: Any = None
_registered = False
_refusal = None


class Settings:
    framing_values = staticmethod(settings.framing.snapshot)
    third_person_ads = staticmethod(settings.ads.enabled)
    orbit_distance = staticmethod(settings.zoom.distance)
    set_orbit_distance = staticmethod(settings.zoom.save)
    loot_distance = staticmethod(settings.loot_distance)
    speed_fov = staticmethod(settings.speed_fov.values)
    dynamic_camera = staticmethod(settings.dynamic.values)
    fov_enabled = staticmethod(settings.custom_fov_enabled)
    fov_value = staticmethod(settings.fov_value)
    saved_fov_pair = staticmethod(settings.saved_fov_pair)
    remember_fov_pair = staticmethod(settings.remember_fov_pair)
    third_person_enabled = staticmethod(settings.third_person_enabled)
    set_third_person = staticmethod(settings.set_third_person)
    shoulder_left = staticmethod(settings.shoulder_left_enabled)
    shoulder_transition = staticmethod(settings.shoulder_transition.seconds)
    orbit_transition = staticmethod(settings.shoulder_transition.orbit_seconds)
    set_shoulder_left = staticmethod(settings.set_shoulder_left)
    orbit_enabled = staticmethod(settings.orbit_enabled)
    set_orbit = staticmethod(settings.set_orbit)
    reject_orbit = staticmethod(settings.reject_orbit)
    note = staticmethod(report.note)


ADAPTER = Settings()


def start() -> IncompatibleState | None:
    global _runtime, _registered, _refusal
    if _registered or _refusal is not None:
        return _refusal
    try:
        _runtime = shared()
    except IncompatibleState as error:
        # Keep the pack usable; a refused camera must never acquire or replace another authority.
        _runtime, _refusal = None, error
        settings.framing.confirm = lambda _restoring=False: False
        report.error_once("camera_protocol", error.message)
        return error
    _runtime.register(OWNER, PRIORITY, ADAPTER, PROTOCOL)
    settings.framing.confirm = lambda restoring=False: confirm_settings(_runtime, OWNER, ADAPTER, restoring)
    _registered = True


def on_frame(now_ns: int) -> None:
    if not _registered:
        start()
    if not _registered:
        return
    setup_error = _runtime.prepare_third_person(
        OWNER, settings.third_person_enabled(), ensure)
    _runtime.tick(get_pc(possibly_loading=True), now_ns)
    if setup_error is not None:
        raise setup_error


def toggle_third_person() -> bool:
    return bool(_registered and _runtime.toggle_third_person(OWNER))


def base_view_locked() -> bool:
    return bool(_registered and _runtime.base_view_locked(OWNER))


def toggle_shoulder() -> bool:
    return bool(_registered and _runtime.toggle_shoulder(OWNER))


def set_shoulder(left: bool) -> bool:
    return bool(_registered and _runtime.set_shoulder(OWNER, left))


def toggle_orbit() -> bool:
    return bool(_registered and _runtime.toggle_orbit(OWNER))


def set_orbit(enabled: bool) -> bool:
    return bool(_registered and _runtime.set_orbit(OWNER, enabled))


def cancel_orbit(*, restore: bool = True) -> bool:
    return bool(_registered and (_runtime.cancel_orbit(OWNER) if restore
                                else _runtime.cancel_orbit(OWNER, restore=False)))


def ready() -> bool:
    return bool(_registered and _runtime.camera_ready(OWNER))


def adjust_orbit_zoom(direction: int) -> bool:
    return bool(_registered and _runtime.adjust_orbit_zoom(OWNER, direction))


def elected_elsewhere() -> bool:
    """Do not expose settings that cannot control the currently elected camera."""
    if _refusal is not None:
        return True
    owner = elected()
    return owner is not None and owner != OWNER


def aim_status() -> tuple[str, str] | None:
    if _refusal is not None:
        from . import panel_i18n
        return _refusal.notice, panel_i18n.text(_refusal.notice, "EN")
    reason = _runtime.ads_status(OWNER) if _registered else None
    return (reason, ADS_NOTICES[reason]) if reason is not None else None


def framing_status():
    if _refusal is not None:
        return _refusal.notice
    controller = getattr(_runtime, "third_person", None) if _registered else None
    framing = getattr(controller, "framing", None)
    if framing is None and getattr(controller, "_bridge_started", False):
        return "unavailable"
    return framing.reason if framing is not None else None


def stop() -> None:
    global _registered, _refusal
    _refusal = None
    if not _registered:
        settings.framing.confirm = lambda _restoring=False: True
        return
    try:
        _runtime.unregister(OWNER)
    finally:
        _registered = False
        settings.framing.confirm = lambda _restoring=False: True
