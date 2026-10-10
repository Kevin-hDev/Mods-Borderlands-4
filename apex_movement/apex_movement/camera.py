"""Full Apex Movement pack adapter to the process-wide camera runtime."""

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

from . import camera_settings, pack, report

OWNER = "apex_movement"
PRIORITY = 200
_runtime: Any = None
_registered = False
_refusal = None


class Settings:
    framing_values = staticmethod(camera_settings.framing.snapshot)
    third_person_ads = staticmethod(camera_settings.ads.enabled)
    orbit_distance = staticmethod(camera_settings.zoom.distance)
    set_orbit_distance = staticmethod(camera_settings.zoom.save)
    camera_distance = staticmethod(camera_settings.distance.index)
    camera_distances = staticmethod(camera_settings.distance.distances)
    look_sensitivity = staticmethod(camera_settings.sensitivity.values)
    sniper_optics = staticmethod(camera_settings.optics.sniper_ticked)
    weapon_optics = staticmethod(camera_settings.optics.weapon_ticked)
    sniper_zoom_keys = staticmethod(camera_settings.optics.keys)
    set_camera_distance = staticmethod(camera_settings.distance.save)
    loot_distance = staticmethod(camera_settings.loot_distance)
    speed_fov = staticmethod(camera_settings.speed_fov.values)
    dynamic_camera = staticmethod(camera_settings.dynamic.values)
    omni_direction = staticmethod(camera_settings.omni.values)
    free_look = staticmethod(camera_settings.free_look.values)
    fov_enabled = staticmethod(camera_settings.custom_fov_enabled)
    fov_value = staticmethod(camera_settings.fov_value)
    saved_fov_pair = staticmethod(camera_settings.saved_fov_pair)
    remember_fov_pair = staticmethod(camera_settings.remember_fov_pair)
    third_person_enabled = staticmethod(camera_settings.third_person_enabled)
    set_third_person = staticmethod(camera_settings.set_third_person)
    shoulder_left = staticmethod(camera_settings.shoulder_left_enabled)
    shoulder_transition = staticmethod(camera_settings.shoulder_transition.seconds)
    shoulder_auto = staticmethod(camera_settings.shoulder_transition.automatic.values)
    orbit_transition = staticmethod(camera_settings.shoulder_transition.orbit_seconds)
    set_shoulder_left = staticmethod(camera_settings.set_shoulder_left)
    orbit_enabled = staticmethod(camera_settings.orbit_enabled)
    set_orbit = staticmethod(camera_settings.set_orbit)
    reject_orbit = staticmethod(camera_settings.reject_orbit)
    note = staticmethod(report.note)


ADAPTER = Settings()


def start() -> IncompatibleState | None:
    global _runtime, _registered, _refusal
    if _registered or _refusal is not None or not pack.is_full():
        return _refusal
    try:
        _runtime = shared()
    except IncompatibleState as error:
        # Keep the pack usable; a refused camera must never acquire or replace another authority.
        _runtime, _refusal = None, error
        camera_settings.framing.confirm = lambda _restoring=False: False
        report.error_once("camera_protocol", error.message)
        return error
    _runtime.register(OWNER, PRIORITY, ADAPTER, PROTOCOL)
    camera_settings.framing.confirm = lambda restoring=False: confirm_settings(_runtime, OWNER, ADAPTER, restoring)
    _registered = True


def on_frame(now_ns: int) -> None:
    if not pack.is_full():
        return
    if not _registered:
        start()
    if not _registered:
        return
    setup_error = _runtime.prepare_third_person(
        OWNER, camera_settings.third_person_enabled(), ensure)
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


def cycle_camera_distance() -> bool:
    # The shared runtime may come from an older mod's copy, made before the camera distance key (2026-10-07).
    cycle = getattr(_runtime, "cycle_camera_distance", None) if _registered else None
    return bool(callable(cycle) and cycle(OWNER))


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


def in_third_person() -> bool:
    """The game shows the third-person view on foot, as the shared runtime last read it (omni_direction.py); False
    with a runtime from an older mod's copy, which does not read it."""
    omni = getattr(_runtime, "omni", None) if _registered else None
    return getattr(omni, "third_person", False) is True


def elected_elsewhere() -> bool:
    if _refusal is not None:
        return True
    owner = elected()
    return owner is not None and owner != OWNER


def stop() -> None:
    global _registered, _refusal
    _refusal = None
    if not _registered:
        camera_settings.framing.confirm = lambda _restoring=False: True
        return
    try:
        _runtime.unregister(OWNER)
    finally:
        _registered = False
        camera_settings.framing.confirm = lambda _restoring=False: True
