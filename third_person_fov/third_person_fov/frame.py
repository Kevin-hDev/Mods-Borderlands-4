"""Clock the shared camera from the played body, never from enemy animations."""

import time
from typing import Any

from mods_base import get_pc, hook
from unrealsdk.hooks import Type

try:
    from .apex_camera_runtime.played_body import PlayedBody, address
except ModuleNotFoundError as error:
    if error.name != f"{__package__}.apex_camera_runtime":
        raise
    from apex_camera_runtime.played_body import PlayedBody, address

from . import camera, report

HOOK_PATH = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
_in_game = False
_played = PlayedBody()


def reset() -> None:
    global _in_game
    _in_game = False
    _played.forget()


def on_frame(obj: Any, now_ns: int) -> None:
    global _in_game
    if not _played.must_ask(obj, now_ns):
        return
    obj_address = address(obj)
    pc = get_pc(possibly_loading=True)
    character = getattr(pc, "OakCharacter", None) if pc is not None else None
    if character is None:
        _played.forget()
        if _in_game:
            _in_game = False
            camera.on_frame(now_ns, pc)
        return
    mesh = getattr(character, "Mesh", None)
    body = mesh.GetAnimInstance() if mesh is not None else None
    # The live body is authoritative because player animation subclasses vary by character and state.
    if body is None or address(body) != obj_address:
        if obj_address == _played.body:
            _played.forget()
        return
    _played.remember(obj_address, address(getattr(body, "Outer", None)), now_ns)
    _in_game = True
    camera.on_frame(now_ns, pc)


@hook(HOOK_PATH, Type.POST, hook_identifier=f"{__package__}:frame")
def tick(obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    try:
        on_frame(obj, time.perf_counter_ns())
    except Exception as exc:
        report.error_once("camera", f"camera update skipped after an error: {exc!r}")
