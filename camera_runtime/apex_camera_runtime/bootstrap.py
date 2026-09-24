"""Wire game SDK services to the shared camera runtime once."""

from pathlib import Path
from typing import Any, Callable

from .collision import CollisionGuard
from .native_bridge import Bridge, load_packaged_library
from .third_person import ThirdPersonController

IDENTIFIER = "apex_camera_runtime"


def attach(runtime: Any, library: Any, hooks: Any, sdk: Any, weak_ref: Callable,
           kismet: Any, log: Callable[[str], None]) -> ThirdPersonController:
    if runtime.third_person is not None:
        return runtime.third_person
    bridge = Bridge(library)
    collision = CollisionGuard(kismet, sdk, log)
    controller = ThirdPersonController(
        hooks, bridge, IDENTIFIER, weak_ref=weak_ref, log=log, collision=collision)
    runtime.set_third_person(controller)
    return controller


def ensure(runtime: Any) -> ThirdPersonController:
    import unrealsdk
    from mods_base import MODS_DIR
    from unrealsdk import hooks, logging
    from unrealsdk.unreal import WeakPointer

    if runtime.third_person is not None:
        return runtime.third_person
    library = load_packaged_library(Path(MODS_DIR) / "_apex_camera_runtime")
    kismet = unrealsdk.find_class("KismetSystemLibrary").ClassDefaultObject
    log = lambda message: logging.info(f"[Camera Runtime] {message}")
    return attach(runtime, library, hooks, unrealsdk, WeakPointer, kismet, log)
