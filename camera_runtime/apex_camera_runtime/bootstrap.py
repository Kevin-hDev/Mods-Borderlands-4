"""Wire game SDK services to the shared camera runtime once."""

from pathlib import Path
from typing import Any, Callable

from .collision import CollisionGuard
from .camera_bridge import CameraBridge
from .interaction_bridge import InteractionBridge, load_library as load_interaction_library
from .generated_limits import RUNTIME_FOLDER
from .native_bridge import Bridge, load_packaged_library
from .third_person import ThirdPersonController

IDENTIFIER = "apex_camera_runtime"


def attach(runtime: Any, library: Any, interaction_library: Any, hooks: Any, sdk: Any, weak_ref: Callable,
           kismet: Any, log: Callable[[str], None]) -> ThirdPersonController:
    if runtime.third_person is not None:
        return runtime.third_person
    try:
        interaction = InteractionBridge(interaction_library) if interaction_library is not None else None
    except Exception as error:
        # No native start has run yet; CameraBridge reports degraded operation on activation.
        interaction = None
        log(f"interaction alignment setup failed: {type(error).__name__}")
    bridge = CameraBridge(Bridge(library), interaction, log)
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
    log = lambda message: logging.info(f"[Camera Runtime] {message}")
    runtime_folder = Path(MODS_DIR) / RUNTIME_FOLDER
    library = load_packaged_library(runtime_folder)
    try:
        interaction_library = load_interaction_library(runtime_folder)
    except Exception as error:
        # Optional alignment must not prevent loading the existing framing feature.
        interaction_library = None
        log(f"interaction alignment load failed: {type(error).__name__}")
    kismet = unrealsdk.find_class("KismetSystemLibrary").ClassDefaultObject
    return attach(runtime, library, interaction_library, hooks, unrealsdk, WeakPointer, kismet, log)
