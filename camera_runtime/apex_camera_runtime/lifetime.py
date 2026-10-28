"""Weak ownership and identity checks for one live player-camera unit."""

from typing import Any, Callable


class CameraLifetime:
    def __init__(self, weak_ref: Callable) -> None:
        self.weak_ref = weak_ref
        self.pc_ref = self.actor_ref = self.manager_ref = None
        self.ids = (0, 0, 0)

    @staticmethod
    def address(value: Any) -> int:
        if value is None:
            return 0
        try:
            return int(value._get_address())
        except (AttributeError, TypeError, ValueError):
            return id(value)

    def bind(self, pc: Any, actor: Any, manager: Any) -> None:
        self.pc_ref = self.weak_ref(pc)
        self.actor_ref = self.weak_ref(actor)
        self.manager_ref = self.weak_ref(manager)
        self.ids = self.address(pc), self.address(actor), self.address(manager)

    def inspect(self, pc: Any) -> tuple[Any, Any, Any, tuple[int, int, int], bool]:
        current = self.pc_ref() if self.pc_ref is not None else None
        actor = getattr(pc, "OakCharacter", None)
        manager = getattr(pc, "PlayerCameraManager", None)
        target = self.address(pc), self.address(actor), self.address(manager)
        changed = (current is None or any(value <= 0 for value in target)
                   or target != self.ids)
        return current, actor, manager, target, changed

    def owned(self) -> tuple[Any, Any]:
        actor = self.actor_ref() if self.actor_ref is not None else None
        manager = self.manager_ref() if self.manager_ref is not None else None
        return actor, manager

    def clear(self) -> None:
        self.pc_ref = self.actor_ref = self.manager_ref = None
        self.ids = (0, 0, 0)
