"""Priority-300 adapter to the process-wide camera runtime."""

from typing import Any

from mods_base import get_pc

try:
    from .apex_camera_runtime.bootstrap import ensure
    from .apex_camera_runtime.constants import PROTOCOL
    from .apex_camera_runtime.shared import shared
except ModuleNotFoundError as error:
    if error.name != f"{__package__}.apex_camera_runtime":
        raise
    from apex_camera_runtime.bootstrap import ensure
    from apex_camera_runtime.constants import PROTOCOL
    from apex_camera_runtime.shared import shared

from . import report, settings

OWNER = "third_person_fov"
PRIORITY = 300
_runtime: Any = None
_registered = False


class Settings:
    fov_enabled = staticmethod(settings.custom_fov_enabled)
    fov_value = staticmethod(settings.fov_value)
    saved_fov_pair = staticmethod(settings.saved_fov_pair)
    remember_fov_pair = staticmethod(settings.remember_fov_pair)
    third_person_enabled = staticmethod(settings.third_person_enabled)
    set_third_person = staticmethod(settings.set_third_person)
    note = staticmethod(report.note)


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
