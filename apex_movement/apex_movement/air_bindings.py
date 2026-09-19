"""Binds the game's own crouch and jump keys through the SDK, so the air rule sees each press before the game.

The keys come from the game's input list rather than fixed names, so the rule follows the player's own key choices.
air_crouch reads the list again every second and binds again when it changes: read only once, at a vehicle exit it
lacked the gamepad's crouch key, which stayed unbound until the next level (2026-09-18).
Verified in session 4 (2026-09-16): a press blocked here never reaches the game, and nothing can send a fake release.
"""

import time
from typing import Any

from mods_base import keybind
from unrealsdk.hooks import Block

from . import air_keys, game, report

CROUCH_ACTIONS = ("Action_Crouch_Hold", "Action_Crouch", "Action_CrouchOrDash")
JUMP_ACTIONS = ("Action_Jump_HoldToGlide",)

_binds: list[Any] = []
# The crouch and jump keys bound, to tell whether the game's list still names the same ones.
_keys: tuple[frozenset[str], frozenset[str]] = (frozenset(), frozenset())


def keys_for(mappings: list[Any], actions: tuple[str, ...]) -> set[str]:
    found: set[str] = set()
    for mapping in mappings:
        action = mapping.Action
        if action is not None and str(action.Name) in actions:
            found.add(str(mapping.Key.KeyName))
    return found


def _on_crouch(key: str) -> Any:
    def callback(event: Any) -> Any:
        try:
            character = game.character()
            if character is None:
                return None
            in_air = game.is_in_air(character.CharacterMovement)
            name = getattr(event, "name", str(event))
            return Block if air_keys.crouch_event(key, name, time.perf_counter_ns(), in_air) else None
        except Exception as exc:
            # A press wrongly blocked makes the game unplayable; a press wrongly passed only does what the game does.
            report.error_once("air_bindings:crouch", f"crouch key passed to the game after an error: {exc!r}")
            return None

    return callback


def _on_jump(event: Any) -> None:
    try:
        air_keys.jump_event(getattr(event, "name", str(event)), time.perf_counter_ns())
    except Exception as exc:
        report.error_once("air_bindings:jump", f"jump key not followed after an error: {exc!r}")


def _wanted(mappings: list[Any]) -> tuple[frozenset[str], frozenset[str]]:
    crouch_keys = frozenset(keys_for(mappings, CROUCH_ACTIONS))
    return crouch_keys, frozenset(keys_for(mappings, JUMP_ACTIONS)) - crouch_keys


def is_bound() -> bool:
    return bool(_binds)


def matches(mappings: list[Any]) -> bool:
    """The keys bound are still the ones the game lists."""
    return _wanted(mappings) == _keys


def bind(mappings: list[Any]) -> bool:
    """Binds every crouch and jump key; False when the game lists no crouch key."""
    global _keys
    crouch_keys, jump_keys = _wanted(mappings)
    if not crouch_keys:
        return False
    # Named after the package, like frame.py's hook, so an identifier names the file that bound it: each separate file
    # has its own package name. The SDK binds by key alone, so two files never clash through these names.
    for key in sorted(crouch_keys):
        _binds.append(keybind(f"{__package__}:crouch:{key}", key, _on_crouch(key), is_hidden=True, event_filter=None))
    for key in sorted(jump_keys):
        _binds.append(keybind(f"{__package__}:jump:{key}", key, _on_jump, is_hidden=True, event_filter=None))
    for bound in _binds:
        bound.enable()
    _keys = (crouch_keys, jump_keys)
    report.note(f"air crouch keys crouch={sorted(crouch_keys)} jump={sorted(jump_keys)}")
    return True


def unbind() -> None:
    global _keys
    _keys = (frozenset(), frozenset())
    count = len(_binds)
    for bound in _binds:
        bound.disable()
    _binds.clear()
    if count:
        report.note(f"air crouch keys released ({count})")
