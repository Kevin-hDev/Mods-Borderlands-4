"""Omni Sprint's own copy of the open sprint, for a game whose shared camera runtime cannot do it.

Since 2026-10-09 the shared runtime owns the sprint limit and the sprint's backward slot for the three camera mods
(docs/omni_direction/spec-omni-direction.md). The runtime that runs is the first mod's copy loaded: an older Apex
Movement or Third Person & FOV beside this Omni Sprint brings one without that unit, and a runtime of another protocol
refuses this mod. In both cases this file runs the same unit from Omni Sprint's own copy, for its switch only, as Omni
Sprint did alone before: the older runtime never writes either value, so there is still one writer.
"""

from typing import Any

try:
    from .apex_camera_runtime import omni_direction
except ModuleNotFoundError as error:
    if error.name != f"{__package__}.apex_camera_runtime":
        raise
    from apex_camera_runtime import omni_direction

from . import camera, report

_unit: Any = None


class _Client:
    """The one client of the private unit: Omni Sprint's settings, the body left to the game."""

    settings = camera.ADAPTER


def needed() -> bool:
    runtime = camera._runtime if camera._registered else None
    return runtime is None or getattr(runtime, "omni", None) is None


def tick(pc: Any, now_ns: int) -> None:
    global _unit
    if not needed():
        stop()
        return
    if _unit is None:
        _unit = omni_direction.OmniDirection(omni_direction.game_modules, f"{__package__}:omni_direction")
        report.note("shared camera runtime without the open sprint: Omni Sprint opens it on its own")
    # No camera controller: the private unit never turns the body, it only opens the sprint and fills the slot.
    _unit.sync((_Client,), camera.ADAPTER, pc, None, now_ns)


def stop() -> None:
    global _unit
    unit, _unit = _unit, None
    if unit is not None:
        unit.stop()
