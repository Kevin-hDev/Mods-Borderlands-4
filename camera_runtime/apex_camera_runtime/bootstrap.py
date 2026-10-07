"""Wire game SDK services to the shared camera runtime once."""

from pathlib import Path
from typing import Any, Callable

from .collision import CollisionResolver
from .climb_anchor import ClimbAnchorSession
from .ads_bridge import AdsBridge
from .build_preflight import BuildPreflight
from .ads_context import ContextReader
from .ads_session import AdsSession
from .camera_bridge import CameraBridge
from .framing_bridge import FramingBridge
from .framing_session import FramingSession
from .framing_status import START_FAILURE
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
    collision = CollisionResolver(kismet, sdk, weak_ref, log)
    preflight = BuildPreflight(library, log)
    preflight.start()
    bridge = CameraBridge(Bridge(library), interaction, log, collision=collision)
    framing = None
    try:
        native_ads = AdsBridge(library, log, preflight=preflight)
        ads = AdsSession(native_ads, ContextReader(weak_ref, native_ads.identify, sdk.find_all), log)
        native_ads.start_preflight()
    except Exception:
        ads = None
        log("Third-person aiming unavailable; native aiming retained.")
    if ads is not None:
        try:
            framing = FramingSession(FramingBridge(library), native_ads, ads.reader, log)
            ads.extra_zoom_pending = framing.bridge.zoom_pending
        except Exception as error:
            log(f"{START_FAILURE}: {type(error).__name__}")
    try:
        anchor = ClimbAnchorSession(library, weak_ref, log)
    except Exception as error:
        anchor = None
        log(f'native climb animated anchor unavailable: {type(error).__name__}')
    controller = ThirdPersonController(
        hooks, bridge, IDENTIFIER, weak_ref=weak_ref, log=log, ads=ads, framing=framing,
        anchor=anchor, readiness=preflight.ready)
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
