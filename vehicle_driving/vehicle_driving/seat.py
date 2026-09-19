"""The vehicle the player drives, or None on foot, while loading, or before a player exists.

At the wheel, the controller's pawn is the vehicle and it has an OakVehicleMovement (session 1, 2026-09-18, verified
in game); on foot the pawn is the character, which has none.
"""

from typing import Any


def driven_vehicle(pc: Any) -> Any:
    vehicle = getattr(pc, "Pawn", None) if pc is not None else None
    return vehicle if getattr(vehicle, "OakVehicleMovement", None) is not None else None
