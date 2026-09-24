"""Omni Sprint's adapter to the process-wide camera runtime."""

from typing import Any

from mods_base import get_pc

try:
    from .apex_camera_runtime.bootstrap import ensure
    from .apex_camera_runtime.constants import PROTOCOL
    from .apex_camera_runtime.shared import shared
except ModuleNotFoundError as error:
    # Source tests use the canonical sibling source; packaged builds carry it below the mod's only SDK root.
    if error.name != f"{__package__}.apex_camera_runtime":
        raise
    from apex_camera_runtime.bootstrap import ensure
    from apex_camera_runtime.constants import PROTOCOL
    from apex_camera_runtime.shared import shared

from . import report, settings

OWNER = "omni_sprint"
PRIORITY = 100
_runtime: Any = None
_registered = False


class Settings:
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
    def note(message: str) -> None:
        report.note(message)


ADAPTER = Settings()


def start() -> None:
    global _runtime, _registered
    if _registered:
        return
    _runtime = shared()
    _runtime.register(OWNER, PRIORITY, ADAPTER, PROTOCOL)
    _registered = True


def on_frame(now_ns: int) -> None:
    if not _registered:
        start()
    setup_error = _runtime.prepare_third_person(
        OWNER, settings.third_person_enabled(), ensure)
    _runtime.tick(get_pc(possibly_loading=True), now_ns)
    if setup_error is not None:
        raise setup_error


def toggle_third_person() -> bool:
    return bool(_registered and _runtime.toggle_third_person(OWNER))


def stop() -> None:
    global _registered
    if not _registered:
        return
    try:
        _runtime.unregister(OWNER)
    finally:
        _registered = False
