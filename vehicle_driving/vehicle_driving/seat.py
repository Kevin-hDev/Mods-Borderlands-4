"""The vehicle the player drives, or None on foot, while loading, or before a player exists; and whether this game is a
co-op guest's.

At the wheel, the controller's pawn is the vehicle and it has an OakVehicleMovement (session 1, 2026-09-18, verified
in game); on foot the pawn is the character, which has none.
"""

from typing import Any

import unrealsdk
from unrealsdk.unreal import WeakPointer


def driven_vehicle(pc: Any) -> Any:
    vehicle = getattr(pc, "Pawn", None) if pc is not None else None
    if vehicle is None or WeakPointer(vehicle)() is None:
        # A vehicle the game destroyed can stay the pawn a moment: taken, it would be taken again every frame, since the
        # values' owner already reads it as gone (not seen in game, review of 2026-09-25).
        return None
    return vehicle if getattr(vehicle, "OakVehicleMovement", None) is not None else None


def on_guest_game(vehicle: Any) -> bool:
    """Whether this game is a co-op guest's: the host has the authority on every vehicle there. The driver's attributes
    the host writes come back to the guest's game; written again there, they were multiplied a second time, 132.7
    becoming 334.5 (trial 2 of docs/coop/2026-10-17-vehicule-invite.md, verified in game)."""
    return vehicle.GetLocalRole() != unrealsdk.find_enum("ENetRole").ROLE_Authority
