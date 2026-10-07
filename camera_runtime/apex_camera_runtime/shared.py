"""Create one runtime even when two sdkmod archives carry this package."""

import sys
from types import ModuleType
from typing import Callable

from .constants import MAX_PROTOCOL_NOTE_VALUE, PROTOCOL
from .fov import FovEngine
from .runtime import CameraRuntime

# ADS changes native structures and ownership: old runtimes cannot join this authority.
STATE = f"_apex_camera_runtime_v{PROTOCOL}"
LEGACY_STATES = tuple(f"_apex_camera_runtime_v{version}" for version in range(1, PROTOCOL))
ALL_STATES = (STATE, *LEGACY_STATES)


class IncompatibleState(RuntimeError):
    """A loaded mod carries a camera runtime of another protocol: the player has to update one of the two."""

    # The line a settings window shows for this refusal, in place of its line for an unknown cause.
    notice = "camera_outdated"
    message = "camera unavailable: update the camera mods to matching versions and restart the game"


def _existing_state() -> ModuleType | None:
    found = [sys.modules[name] for name in ALL_STATES if name in sys.modules]
    if not found:
        return None
    state = found[0]
    if (any(getattr(item, "protocol", None) != PROTOCOL for item in found)
            or any(item is not state for item in found[1:])):
        refusal = IncompatibleState("incompatible shared camera state")
        # Log bounded numeric protocols, never a foreign object's repr or name.
        protocols = tuple(getattr(item, "protocol", None) for item in found)
        labels = tuple(str(value) if type(value) is int and 0 < value <= MAX_PROTOCOL_NOTE_VALUE
                       else "unknown" for value in protocols)
        refusal.message += (f"; expected_protocol={PROTOCOL}; "
                            f"loaded_protocols={','.join(dict.fromkeys(labels))}")
        raise refusal
    return state


def shared(weak_ref: Callable | None = None, address_of: Callable | None = None) -> CameraRuntime:
    state = _existing_state()
    if state is not None:
        return state.runtime
    if weak_ref is None:
        from unrealsdk.unreal import WeakPointer
        weak_ref = WeakPointer
    if address_of is None:
        address_of = lambda item: int(item._get_address())
    state = ModuleType(STATE)
    state.protocol = PROTOCOL
    state.runtime = CameraRuntime(FovEngine(weak_ref, address_of))
    from .loot_runtime import LootRuntime
    from .loot_unit import create_unit
    state.runtime.loot = LootRuntime(create_unit)
    from .vehicle_framing import VehicleFraming, game_modules
    state.runtime.vehicle = VehicleFraming(game_modules)
    from . import free_look
    state.runtime.free_look = free_look.FreeLook(free_look.game_modules)
    from . import ads_category, ads_paths_reader, generated_ads
    state.ads_category_reader = ads_category.category
    state.ads_object_address = ads_category.address
    state.ads_paths_reader = (generated_ads.PathsConfig, generated_ads.PathsSample,
                              ads_paths_reader.make_config, ads_paths_reader.object_parts)
    for name in ALL_STATES:
        sys.modules[name] = state
    return state.runtime


def elected() -> str | None:
    """The mod whose camera settings apply, or None. Asking never creates the runtime: a menu opens before any
    camera work starts, and while its mod is switched off."""
    state = sys.modules.get(STATE)
    if state is None or getattr(state, "protocol", None) != PROTOCOL:
        return None
    client = state.runtime.arbiter.active()
    return None if client is None else client.owner


def reset_for_tests() -> None:
    state = next((sys.modules[name] for name in ALL_STATES if name in sys.modules), None)
    if state is not None:
        state.runtime.stop()
        for name in ALL_STATES:
            if sys.modules.get(name) is state:
                del sys.modules[name]
