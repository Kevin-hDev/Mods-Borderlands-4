"""The vehicle the player drives, or None on foot, while loading, or before a player exists; and whether this game is a
co-op guest's.

At the wheel, the controller's pawn is the vehicle and it has an OakVehicleMovement (session 1, 2026-09-18, verified
in game); on foot the pawn is the character, which has none.
"""

from typing import Any

import unrealsdk
from unrealsdk.unreal import WeakPointer

MOVEMENT = "OakVehicleMovement"
# The classes met on foot are the hunters' characters and a few others; past this the memory starts again.
MAX_FOOT_CLASSES = 16

# The classes that have no OakVehicleMovement field at all, by address, each held weakly: another class may take the
# address of one the game destroyed. Asked for a field its class lacks, a character makes the SDK look through its
# class's fields and raise, at every frame on foot (deduced from the SDK, never measured:
# docs/performance/enquetes/2026-10-24-cout-vehicle-driving.md).
_on_foot: dict[int, Any] = {}
_authority: Any = None


def is_vehicle(pawn: Any) -> bool:
    """Whether a pawn has an OakVehicleMovement. A field present but empty is never remembered: a vehicle's class has
    the field even while its movement is not there yet."""
    cls = pawn.Class
    address = cls._get_address()
    remembered = _on_foot.get(address)
    if remembered is not None and remembered() is not None:
        return False
    try:
        movement = getattr(pawn, MOVEMENT)
    except AttributeError:
        if len(_on_foot) >= MAX_FOOT_CLASSES:
            _on_foot.clear()
        _on_foot[address] = WeakPointer(cls)
        return False
    return movement is not None


def driven_vehicle(pc: Any) -> Any:
    vehicle = getattr(pc, "Pawn", None) if pc is not None else None
    if vehicle is None or WeakPointer(vehicle)() is None:
        # A vehicle the game destroyed can stay the pawn a moment: taken, it would be taken again every frame, since the
        # values' owner already reads it as gone (not seen in game, review of 2026-09-25).
        return None
    return vehicle if is_vehicle(vehicle) else None


def authority() -> Any:
    """The engine's ROLE_Authority, the same for the whole game: looked up once rather than at every frame."""
    global _authority
    if _authority is None:
        _authority = unrealsdk.find_enum("ENetRole").ROLE_Authority
    return _authority


def on_guest_game(vehicle: Any) -> bool:
    """Whether this game is a co-op guest's: the host has the authority on every vehicle there. The driver's attributes
    the host writes come back to the guest's game; written again there, they were multiplied a second time, 132.7
    becoming 334.5 (trial 2 of docs/coop/2026-10-17-vehicule-invite.md, verified in game)."""
    return vehicle.GetLocalRole() != authority()
