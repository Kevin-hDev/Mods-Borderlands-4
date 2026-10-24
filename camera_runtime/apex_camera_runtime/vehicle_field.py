"""Tells a vehicle from a character by its OakVehicleMovement field, for the units clocked by every animation update.

A character's class has no such field: asking for it raised inside the SDK at every frame, twice (Free Look and the
framing at the wheel). The classes found without it are kept, and only those (2026-10-24). A vehicle's field is still
read each time: it may be empty while the vehicle is being built.
"""

from typing import Any, Callable

# Bounded: the handful of character classes of a game; a full set is emptied and found again.
MAX_CLASSES = 32


class VehicleField:
    def __init__(self, address_of: Callable[[Any], int]) -> None:
        self.address_of = address_of
        self.without: set[int] = set()

    def movement(self, pawn: Any) -> Any:
        """The pawn's vehicle movement, or None for a character or a vehicle not built yet."""
        pawn_class = getattr(pawn, "Class", None)
        key = self.address_of(pawn_class) if pawn_class is not None else 0
        if key and key in self.without:
            return None
        try:
            return pawn.OakVehicleMovement
        except AttributeError:
            if key:
                if len(self.without) >= MAX_CLASSES:
                    self.without.clear()
                self.without.add(key)
            return None
