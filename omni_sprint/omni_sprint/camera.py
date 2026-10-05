"""Omni Sprint's adapter to the process-wide camera runtime."""

from typing import Any

from mods_base import get_pc

try:
    from .apex_camera_runtime.option_texts import ADS_NOTICES
    from .apex_camera_runtime.bootstrap import ensure
    from .apex_camera_runtime.framing_session import confirm_settings
    from .apex_camera_runtime.constants import PROTOCOL
    from .apex_camera_runtime.shared import IncompatibleState, elected, shared
except ModuleNotFoundError as error:
    # Source tests use the canonical sibling source; packaged builds carry it below the mod's only SDK root.
    if error.name != f"{__package__}.apex_camera_runtime":
        raise
    from apex_camera_runtime.option_texts import ADS_NOTICES
    from apex_camera_runtime.bootstrap import ensure
    from apex_camera_runtime.framing_session import confirm_settings
    from apex_camera_runtime.constants import PROTOCOL
    from apex_camera_runtime.shared import IncompatibleState, elected, shared

from . import report, settings

OWNER = "omni_sprint"
PRIORITY = 100
_runtime: Any = None
_registered = False
_refusal = None


class Settings:
    framing_values = staticmethod(settings.framing.snapshot)
    third_person_ads = staticmethod(settings.ads.enabled)
    orbit_distance = staticmethod(settings.zoom.distance)
    set_orbit_distance = staticmethod(settings.zoom.save)
    loot_distance = staticmethod(settings.loot_distance)
    @staticmethod
    def fov_enabled() -> bool:
        return settings.custom_fov_enabled()

    @staticmethod
    def fov_value() -> float:
        return settings.fov_value()

    @staticmethod
    def saved_fov_pair():
        return settings.saved_fov_pair()

    @staticmethod
    def remember_fov_pair(native: float, applied: float) -> None:
        settings.remember_fov_pair(native, applied)

    @staticmethod
    def third_person_enabled() -> bool:
        return settings.third_person_enabled()

    @staticmethod
    def set_third_person(value: bool) -> None:
        settings.set_third_person(value)

    @staticmethod
    def shoulder_left() -> bool:
        return settings.shoulder_left_enabled()

    @staticmethod
    def set_shoulder_left(value: bool) -> None:
        settings.set_shoulder_left(value)

    @staticmethod
    def orbit_enabled() -> bool:
        return settings.orbit_enabled()

    @staticmethod
    def set_orbit(value: bool) -> None:
        settings.set_orbit(value)

    @staticmethod
    def reject_orbit() -> None:
        settings.reject_orbit()

    @staticmethod
    def note(message: str) -> None:
        report.note(message)


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
    """True while another registered mod's higher-priority camera settings are applied."""
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
