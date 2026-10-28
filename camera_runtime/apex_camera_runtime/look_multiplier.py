"""One key's look multiplier, scaled by the third-person factor (look_sensitivity.py), the game's value kept aside.

The game makes the multiplier at run time, an InputModifierScalar on Action_Look's key, in memory only (probe 2,
releves/2026-10-07-sensibilite). The mouse's Mouse2D has one; the controller's Gamepad_Right2D has two, after the
stick's acceleration, the last one after the frame time (0.8, 0.5) then (60, 60): scaling the last one scales the turn
without bending the acceleration curve. A value the game writes meanwhile becomes the new base, so the player's
setting is never lost.
"""

import math
from typing import Any, Callable

LOOK_ACTION, SCALAR = "Action_Look", "InputModifierScalar"
# The game's list is looked through again each second: rebinding a key or loading a map makes new modifiers.
FIND_NS = 1_000_000_000
MAX_MAPPINGS = 1024
MAX_MODIFIERS = 32


def same(first: tuple, second: tuple) -> bool:
    """A float read back may differ in its last digits: taking that for a game write would compound the factor."""
    return all(math.isclose(a, b, rel_tol=1e-4, abs_tol=1e-9) for a, b in zip(first, second))


def read(modifier: Any) -> tuple:
    value = modifier.Scalar
    return float(value.X), float(value.Y), float(value.Z)


def write(modifier: Any, values: tuple) -> None:
    value = modifier.Scalar
    value.X, value.Y, value.Z = values


class LookMultiplier:
    def __init__(self, key: str, weak_ref: Callable, address_of: Callable) -> None:
        self.key = key
        self.weak_ref, self.address_of = weak_ref, address_of
        self.reset()

    def reset(self) -> None:
        self.ref, self.address = None, 0
        self.base: tuple | None = None
        self.written: tuple | None = None
        self.next_find_ns = 0
        self.missing_context = None

    def apply(self, modifier: Any, wanted_factor: float) -> None:
        current = read(modifier)
        if self.written is None or not same(current, self.written):
            self.base = current
        if wanted_factor == 1.0:
            if self.written is not None:
                write(modifier, self.base)
                self.written = None
            return
        wanted = tuple(axis * wanted_factor for axis in self.base)
        if not same(current, wanted):
            write(modifier, wanted)
        self.written = wanted

    def locate(self, pc: Any, now_ns: int) -> Any:
        held = self.ref() if self.ref is not None else None
        if now_ns < self.next_find_ns:
            if held is not None:
                return held
            if self.ref is None and self._same_missing_context(pc):
                return None
        # Only a completed, empty search is cached. A failed lookup must still propagate.
        self.missing_context = None
        self.next_find_ns = now_ns + FIND_NS
        found = find(pc, self.key)
        address = self.address_of(found) if found is not None else 0
        if address != self.address or (self.ref is not None and held is None):
            # A new multiplier is the game's own value again: the old one went with its map or binding.
            self.reset()
            self.next_find_ns = now_ns + FIND_NS
            if found is not None:
                self.ref, self.address = self.weak_ref(found), address
        player_input = getattr(pc, "PlayerInput", None)
        if found is None and player_input is not None:
            # Missing keys are retried at the same cadence as present ones, but a new input owner bypasses it.
            # Weak references also detect recycled addresses without keeping a controller/input alive.
            # Without PlayerInput there is no mapping traversal to throttle or input owner to retain.
            self.missing_context = tuple(
                (self.address_of(item), self.weak_ref(item)) if item is not None else (0, None)
                for item in (pc, player_input))
        return found

    def _same_missing_context(self, pc: Any) -> bool:
        if self.missing_context is None:
            return False
        for item, (address, ref) in zip((pc, getattr(pc, "PlayerInput", None)), self.missing_context):
            if (self.address_of(item) if item is not None else 0) != address:
                return False
            if ref is not None and ref() is None:
                return False
        return True

    def stop(self) -> None:
        held = self.ref() if self.ref is not None else None
        try:
            if held is not None and self.written is not None and self.base is not None:
                write(held, self.base)
        finally:
            self.reset()


def find(pc: Any, key: str) -> Any:
    """The last multiplier of Action_Look on this key, or None while no player input exists."""
    player_input = getattr(pc, "PlayerInput", None) if pc is not None else None
    if player_input is None:
        return None
    for index, mapping in enumerate(player_input.EnhancedActionMappings):
        if index >= MAX_MAPPINGS:
            return None
        action = getattr(mapping, "Action", None)
        if action is None or str(action.Name) != LOOK_ACTION or str(mapping.Key.KeyName) != key:
            continue
        found = None
        for position, modifier in enumerate(mapping.Modifiers):
            if position >= MAX_MODIFIERS:
                break
            if modifier is not None and str(modifier.Class.Name) == SCALAR:
                found = modifier
        if found is not None:
            return found
    return None
