"""Omni Sprint's clock: each update of the played body ticks the shared camera runtime, which since 2026-10-09 also
opens the sprint and fills the sprint's backward slot (docs/omni_direction/spec-omni-direction.md); without that
runtime, Omni Sprint's own copy does it (sprint_fallback.py).

The hook is only a clock, as in Apex Movement and Vehicle Driving: every animation update in the world calls it, so
only the played body's own update counts.
"""

import time
from typing import Any

from mods_base import get_pc, hook
from unrealsdk.hooks import Type

from . import camera, report, sprint_fallback

HOOK_PATH = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"

_camera_in_game = False


def reset() -> None:
    global _camera_in_game
    _camera_in_game = False


def played(obj: Any) -> tuple[bool, Any]:
    """Whether this update belongs to the played body, and the player controller. The live body is the authority:
    player animation classes vary by character and state."""
    pc = get_pc(possibly_loading=True)
    character = getattr(pc, "OakCharacter", None) if pc is not None else None
    mesh = getattr(character, "Mesh", None) if character is not None else None
    body = mesh.GetAnimInstance() if mesh is not None else None
    return (body is not None and obj is not None and int(body._get_address()) == int(obj._get_address()),
            pc if character is not None else None)


def stop() -> None:
    reset()
    sprint_fallback.stop()


# The identifier carries the package's name, as Apex Movement's and Vehicle Driving's do on this same function: two
# identifiers never replace each other, so the three mods run each frame.
@hook(HOOK_PATH, Type.POST, hook_identifier=f"{__package__}:frame")
def tick(obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    global _camera_in_game
    now_ns = time.perf_counter_ns()
    try:
        player_frame, pc = played(obj)
    except Exception as exc:
        report.error_once("frame", f"a frame was skipped after an error: {exc!r}")
        return
    update = player_frame
    if update:
        _camera_in_game = True
    elif _camera_in_game and pc is None:
        # The player left the game (title screen, loading): one last tick lets the runtime give everything back.
        _camera_in_game = False
        update = True
    if not update:
        return
    try:
        camera.on_frame(now_ns)
    except Exception as exc:
        report.error_once("camera", f"a camera check was skipped after an error: {exc!r}")
    try:
        sprint_fallback.tick(pc, now_ns)
    except Exception as exc:
        report.error_once("sprint_fallback", f"the open sprint's own copy stopped after an error: {exc!r}")
        try:
            sprint_fallback.stop()
        except Exception as stop_error:
            report.error_once("sprint_fallback_stop", f"and could not give everything back: {stop_error!r}")
