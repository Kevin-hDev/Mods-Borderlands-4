"""Weak game-object pointers shared by Vehicle Driving's test SDK."""

from typing import Any


class WeakPointer:
    """Return the object until the fake game destroys it."""

    made: list["WeakPointer"] = []
    destroyed: list[Any] = []

    def __init__(self, obj: Any = None) -> None:
        self.obj = None if any(obj is gone for gone in WeakPointer.destroyed) else obj
        WeakPointer.made.append(self)

    def __call__(self) -> Any:
        return self.obj


def destroy(obj: Any) -> None:
    """Stand in for the game invalidating every weak pointer to one object."""
    WeakPointer.destroyed.append(obj)
    for pointer in WeakPointer.made:
        if pointer.obj is obj:
            pointer.obj = None
