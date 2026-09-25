"""Create one runtime even when two sdkmod archives carry this package."""

import sys
from types import ModuleType
from typing import Callable

from .constants import PROTOCOL
from .fov import FovEngine
from .runtime import CameraRuntime

STATE = f"_apex_camera_runtime_v{PROTOCOL}"


def shared(weak_ref: Callable | None = None, address_of: Callable | None = None) -> CameraRuntime:
    state = sys.modules.get(STATE)
    if state is not None:
        if getattr(state, "protocol", None) != PROTOCOL:
            raise RuntimeError("incompatible shared camera state")
        return state.runtime
    if weak_ref is None:
        from unrealsdk.unreal import WeakPointer
        weak_ref = WeakPointer
    if address_of is None:
        address_of = lambda item: int(item._get_address())
    state = ModuleType(STATE)
    state.protocol = PROTOCOL
    state.runtime = CameraRuntime(FovEngine(weak_ref, address_of))
    sys.modules[STATE] = state
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
    state = sys.modules.get(STATE)
    if state is not None:
        state.runtime.stop()
        del sys.modules[STATE]
