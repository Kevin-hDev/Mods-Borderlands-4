"""Third Person & FOV: the game's native third-person view and a wider field of view."""

from mods_base import build_mod

from . import camera, frame, report, settings

__version__ = "0.1.0"
__author__ = "kevin-hDev"


def _on_enable() -> None:
    report.reset()
    frame.reset()
    camera.start()
    report.note(f"enabled, version {__version__}")


def _on_disable() -> None:
    try:
        camera.stop()
    except Exception:
        report.error_once("camera_restore", "camera restoration failed")
    frame.reset()
    report.note("disabled")


mod = build_mod(
    name="Third Person & FOV",
    hooks=[frame.tick],
    keybinds=[settings.third_person_bind],
    options=settings.OPTIONS,
    on_enable=_on_enable,
    on_disable=_on_disable,
)

if mod.settings_file is not None and not mod.settings_file.exists():
    mod.enable()
