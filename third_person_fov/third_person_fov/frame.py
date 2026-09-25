"""Clock the shared camera from the played body, never from enemy animations."""

import time
from typing import Any

from mods_base import get_pc, hook
from unrealsdk.hooks import Type

from . import camera, report

HOOK_PATH = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
BODY_CLASS = "BPAnim_Player_3rd_C"
_in_game = False


def reset() -> None:
    global _in_game
    _in_game = False


def _address(item: Any) -> int:
    return int(item._get_address()) if item is not None else 0


def on_frame(obj: Any, now_ns: int) -> None:
    global _in_game
    pc = get_pc(possibly_loading=True)
    character = getattr(pc, "OakCharacter", None) if pc is not None else None
    if character is None:
        if _in_game:
            _in_game = False
            camera.on_frame(now_ns)
        return
    if str(getattr(getattr(obj, "Class", None), "Name", "")) != BODY_CLASS:
        return
    mesh = getattr(character, "Mesh", None)
    body = mesh.GetAnimInstance() if mesh is not None else None
    if body is None or _address(body) != _address(obj):
        return
    _in_game = True
    camera.on_frame(now_ns)


@hook(HOOK_PATH, Type.POST, hook_identifier=f"{__package__}:frame")
def tick(obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    try:
        on_frame(obj, time.perf_counter_ns())
    except Exception as exc:
        report.error_once("camera", f"camera update skipped after an error: {exc!r}")
