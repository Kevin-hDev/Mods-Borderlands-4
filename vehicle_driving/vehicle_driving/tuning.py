"""Owns every game value Vehicle Driving writes: the game's own value is kept at the first write and put back.

Spec section 3.1, on Apex Movement's ownership.py model: the mod is the only authority on the values it writes, and a
value is always written as the game's original times its setting, never as the value in the game times it, so nothing
is ever multiplied twice. The vehicle and its driver are held by weak pointers: a vehicle the game destroyed, such as
one replaced by a vehicle summoned again, is never written again, and its values are forgotten with it.
Spec section 3.2: what the game rewrites is followed, never fought.
"""

from typing import Any

from unrealsdk.unreal import WeakPointer

from . import levers

# Game floats are 32-bit: a value read back differs from the one written by about one part in ten million. One
# further off than this share was written by the game.
TOLERANCE = 1e-5


def same(a: float, b: float) -> bool:
    return abs(a - b) <= TOLERANCE * max(1.0, abs(b))


class Entry:
    def __init__(self, target: levers.Target, original: float) -> None:
        self.target = target
        self.original = original
        self.written = original
        # None until the mod writes, so that the first update always writes.
        self.factor: float | None = None


class Tuning:
    def __init__(self) -> None:
        self._vehicle: Any = None
        self._driver: Any = None
        self._targets: list[levers.Target] = []
        self._entries: dict[str, Entry] = {}

    def vehicle(self) -> Any:
        """The vehicle held, or None when none is or when the game destroyed it."""
        return self._vehicle() if self._vehicle is not None else None

    def holds(self) -> bool:
        """True from take() to put_back(), even once the game destroyed the vehicle: its driver's values wait."""
        return self._vehicle is not None

    def take(self, vehicle: Any) -> list[str]:
        """Puts the vehicle held back first, then holds this one; nothing is written before update()."""
        lines = self.put_back()
        self._vehicle = WeakPointer(vehicle)
        driver = getattr(vehicle, "DriverPawn", None)
        self._driver = WeakPointer(driver) if driver is not None else None
        self._targets, missing = levers.targets(vehicle)
        lines.append(f"driving {vehicle.Name}")
        return lines + [f"{name} not found on {vehicle.Name}: left to the game" for name in missing]

    def update(self, factors: dict[str, float]) -> list[str]:
        """Writes each value as its original times its setting, and follows what the game rewrote.

        What was set goes in one line, from the original: the log's proof that nothing is multiplied twice.
        """
        lines: list[str] = []
        written: list[str] = []
        rebased: set[str] = set()
        for target in self._targets:
            if not self._alive(target.owner):
                continue
            current = getattr(target.holder, target.field)
            entry = self._entries.get(target.key)
            if entry is None:
                entry = self._entries[target.key] = Entry(target, current)
            elif not same(current, entry.written):
                if target.base_key is not None and target.base_key not in rebased:
                    # Recomputed from the mod's base: taken as the original, it would be multiplied a second time.
                    entry.written = current
                    lines.append(f"{target.key} recomputed by the game to {current:.3f}, left to it")
                    continue
                entry.original, entry.written, entry.factor = current, current, None
                rebased.add(target.key)
                lines.append(f"{target.key} rewritten by the game to {current:.3f}, taken as its own")
            factor = factors[target.setting]
            if entry.factor != factor:
                value = entry.original * factor
                setattr(target.holder, target.field, value)
                entry.written, entry.factor = value, factor
                written.append(f"{target.key} {entry.original:.3f}->{value:.3f}")
        if written:
            lines.append("set " + ", ".join(written))
        return lines

    def put_back(self) -> list[str]:
        """Puts back every value whose owner is still alive, then forgets them all; returns one line per failure.

        A destroyed owner's values are forgotten with it: writing into a destroyed object can bring the game down. A
        value that cannot be put back is reported and forgotten too: kept, it would be tied to the next vehicle's
        pointers, and the same write just succeeded when the value was set.
        """
        lines: list[str] = []
        for key, entry in self._entries.items():
            if not self._alive(entry.target.owner):
                continue
            try:
                setattr(entry.target.holder, entry.target.field, entry.original)
            except Exception as exc:
                lines.append(f"could not put back {key}: {exc!r}")
        self._entries.clear()
        self._targets = []
        self._vehicle = self._driver = None
        return lines

    def _alive(self, owner: str) -> bool:
        pointer = self._vehicle if owner == levers.VEHICLE else self._driver
        return pointer is not None and pointer() is not None
