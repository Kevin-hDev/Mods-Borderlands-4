"""Runs each switched-on movement once per frame, on the player only.

A movement that raises is switched off alone and reported once: one broken movement must not take the others down.
A switch turned off in the menu stops its movement at the next frame, which puts its values back.
"""

import time
from typing import Any

from mods_base import hook
from unrealsdk.hooks import Type

from . import game, ownership, report

_movements: list[tuple[str, Any, Any]] = []
_active: set[str] = set()
_failed: set[str] = set()


def register(name: str, option: Any, movement: Any) -> None:
    """A movement module offers update(character, now_ns), stop(character) and reset().

    option None means always on: the slide speed has a slider but no switch (spec, section 3).
    """
    _movements.append((name, option, movement))


def _stop(name: str, movement: Any, character: Any) -> None:
    _active.discard(name)
    try:
        movement.stop(character)
    except Exception as exc:
        report.error_once(f"{name}:stop", f"{name} could not stop cleanly: {exc!r}")


def on_frame(obj: Any, now_ns: int) -> None:
    if game.refresh(now_ns):
        # The old character's values went with it; only the movements' own memory needs clearing.
        ownership.forget_character()
        for _, _, movement in _movements:
            movement.reset()
        _active.clear()
    character = game.character()
    if character is None or obj != game.anim():
        return
    for name, option, movement in _movements:
        if name in _failed:
            continue
        if option is not None and not option.value:
            if name in _active:
                _stop(name, movement, character)
            continue
        _active.add(name)
        try:
            movement.update(character, now_ns)
        except Exception as exc:
            _failed.add(name)
            report.error_once(name, f"{name} switched off after an error: {exc!r}")
            _stop(name, movement, character)


def stop_all() -> list[str]:
    character = game.character()
    for name, _, movement in _movements:
        if name in _active:
            _stop(name, movement, character)
    failures = ownership.restore_all()
    _failed.clear()
    game.forget()
    return failures


@hook("/Script/Engine.AnimInstance:BlueprintUpdateAnimation", Type.POST, hook_identifier="apex_movement:frame")
def tick(obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    on_frame(obj, time.perf_counter_ns())
