"""Tells a vehicle from a character by its OakVehicleMovement field, for the units clocked by every animation update.

A character's class has no such field: asking for it raised inside the SDK at every frame, twice (Free Look and the
framing at the wheel). The classes found without it are kept, and only those (2026-10-24). A vehicle's field is still
read each time: it may be empty while the vehicle is being built.

Each class is kept with a weak pointer, checked at each use: a class unloaded with a save or at the title screen can
leave its address to a vehicle's class, which would then pass for a character's (review of 2026-10-24).
"""

from typing import Any, Callable

# Bounded: the handful of character classes of a game; a full set is emptied and found again.
MAX_CLASSES = 32


class VehicleField:
    def __init__(self, address_of: Callable[[Any], int], weak: Callable[[Any], Callable[[], Any]]) -> None:
        self.address_of, self.weak = address_of, weak
        self.without: dict[int, Callable[[], Any]] = {}

    def movement(self, pawn: Any) -> Any:
        """The pawn's vehicle movement, or None for a character or a vehicle not built yet."""
        pawn_class = getattr(pawn, "Class", None)
        key = self.address_of(pawn_class) if pawn_class is not None else 0
        kept = self.without.get(key) if key else None
        if kept is not None:
            held = kept()
            if held is not None and self.address_of(held) == key:
                return None
            del self.without[key]
        try:
            return pawn.OakVehicleMovement
        except AttributeError:
            if key:
                if len(self.without) >= MAX_CLASSES:
                    self.without.clear()
                self.without[key] = self.weak(pawn_class)
            return None
