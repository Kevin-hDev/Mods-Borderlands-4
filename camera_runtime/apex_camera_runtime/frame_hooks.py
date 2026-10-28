"""One SDK hook after the animation update for every camera unit that follows it.

The game calls BlueprintUpdateAnimation once per animated character and per frame, about 1,500 times a second in a
Horde of 120 (It Follows trial 39), and each Python hook on it costs the SDK about 2.5 µs before any of our code runs
(It Follows trial 40). The camera's units each held their own: up to five at once in third person (2026-10-24). The
units still ask for their hook as before; this front gives the SDK one, and calls each unit in the order it asked.

Every other hook passes straight through. Each copy of the runtime carries its own front, named after its package, so
two mods carrying the runtime never replace each other's hook.
"""

import traceback
from typing import Any, Callable

FRAME = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
IDENTIFIER = f"{__package__}:frame"


class FrameHooks:
    def __init__(self, hooks: Any, log: Callable[[str], None]) -> None:
        self.hooks, self.log = hooks, log
        self.Type = hooks.Type
        self.callbacks: dict[str, Callable] = {}
        self.installed = False

    def __getattr__(self, name: str) -> Any:
        return getattr(self.hooks, name)

    def _shared(self, path: str, kind: Any) -> bool:
        return path == FRAME and kind == self.Type.POST

    def add_hook(self, path: str, kind: Any, identifier: str, callback: Callable) -> None:
        if not self._shared(path, kind):
            self.hooks.add_hook(path, kind, identifier, callback)
            return
        self.callbacks[identifier] = callback
        if not self.installed:
            self.hooks.add_hook(FRAME, self.Type.POST, IDENTIFIER, self.dispatch)
            self.installed = True

    def remove_hook(self, path: str, kind: Any, identifier: str) -> None:
        if not self._shared(path, kind):
            self.hooks.remove_hook(path, kind, identifier)
            return
        self.callbacks.pop(identifier, None)
        if not self.callbacks and self.installed:
            self.hooks.remove_hook(FRAME, self.Type.POST, IDENTIFIER)
            self.installed = False

    def has_hook(self, path: str, kind: Any, identifier: str) -> bool:
        if not self._shared(path, kind):
            return self.hooks.has_hook(path, kind, identifier)
        return identifier in self.callbacks

    def dispatch(self, obj: Any, args: Any, ret: Any, func: Any) -> None:
        # A unit may add or remove hooks while called: each one runs only if still asked for.
        for identifier, callback in tuple(self.callbacks.items()):
            if self.callbacks.get(identifier) is not callback:
                continue
            try:
                callback(obj, args, ret, func)
            except Exception:
                # As the SDK does for a hook of its own: told, and the other units still run.
                self.log(f"{identifier} hook failed:\n{traceback.format_exc(limit=8)}")


_front: FrameHooks | None = None


def front(hooks: Any) -> FrameHooks:
    """This copy's front over the SDK's hooks module, the same for every unit that asks."""
    global _front
    if _front is None or _front.hooks is not hooks:
        from unrealsdk import logging
        _front = FrameHooks(hooks, logging.error)
    return _front
