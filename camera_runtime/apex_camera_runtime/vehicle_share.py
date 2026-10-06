"""The camera offset at the wheel, between the camera mods and Vehicle Driving (dynamic camera plan, 2026-10-06).

One writer per frame: when Vehicle Driving places the camera it writes its view plus the framing published here, and
says so; otherwise the camera mods write the framing alone. Kevin: a player without Vehicle Driving gets the effect,
and with it the chosen view stays the same, the speed's framing added to it. The game also adds its own value to the
offset at the wheel, so a value read there never says who wrote it: only this signal does.

This file's one source is the camera runtime; outils/sync_menu_ui.py copies it into Vehicle Driving as camera_share.py.
The slot lives in sys.modules so that every copy, in any mod archive, reads and writes the same one.
"""

import sys
import time
from types import ModuleType

SLOT = "_apex_vehicle_camera_share_v1"
ZERO = (0.0, 0.0, 0.0)
# Past this, a framing or a writer's signal is from a frame long gone: a mod switched off, the player out of the car.
FRESH_NS = 100_000_000


def _slot() -> ModuleType:
    slot = sys.modules.get(SLOT)
    if slot is None:
        slot = ModuleType(SLOT)
        slot.framing, slot.framing_ns, slot.driver_ns = ZERO, 0, 0
        sys.modules[SLOT] = slot
    return slot


def _fresh(stamp: int) -> bool:
    return stamp > 0 and time.perf_counter_ns() - stamp < FRESH_NS


def publish(framing: tuple) -> None:
    """The camera mods: the framing wanted this frame (forward, right, up), ZERO when none."""
    slot = _slot()
    slot.framing, slot.framing_ns = tuple(float(value) for value in framing), time.perf_counter_ns()


def framing() -> tuple:
    """Vehicle Driving: the framing to add to its view, ZERO when no camera mod publishes one."""
    slot = _slot()
    return slot.framing if _fresh(slot.framing_ns) else ZERO


def claim() -> None:
    """Vehicle Driving: it writes the offset this frame."""
    _slot().driver_ns = time.perf_counter_ns()


def claimed() -> bool:
    """The camera mods: Vehicle Driving writes the offset, so they only publish."""
    return _fresh(_slot().driver_ns)
