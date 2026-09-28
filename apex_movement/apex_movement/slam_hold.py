"""Mutes the game's old held-crouch slam while crouch was pressed on the ground.

The ground press must still reach Action_Crouch and Action_CrouchOrDash so crouching and sliding stay native. Only
Action_Crouch_Hold is muted, and only for the same physical key. The game rebuilds this flag, so update reapplies it
every frame until release, then restores the value which was present before Apex Movement changed it.
"""

from typing import Any, Iterable

from . import game, report

ACTION_NAME = "Action_Crouch_Hold"
MAX_MAPPINGS = 400
MAX_HELD_KEYS = 32
MAX_KEY_LENGTH = 128

# One saved state per Action_Crouch_Hold mapping occurrence. Both collections are bounded by the constants above.
_originals: dict[tuple[str, int], bool] = {}


def _held(held_keys: Iterable[str]) -> frozenset[str]:
    valid: list[str] = []
    for key in held_keys:
        if isinstance(key, str) and 0 < len(key) <= MAX_KEY_LENGTH and key not in valid:
            valid.append(key)
        if len(valid) >= MAX_HELD_KEYS:
            break
    return frozenset(valid)


def _mappings() -> Any:
    controller = game.controller()
    player_input = getattr(controller, "PlayerInput", None) if controller is not None else None
    return getattr(player_input, "EnhancedActionMappings", None)


def _names(entry: Any) -> tuple[str, str] | None:
    action = getattr(entry, "Action", None)
    key = getattr(getattr(entry, "Key", None), "KeyName", None)
    if action is None or key is None or str(action.Name) != ACTION_NAME:
        return None
    key_name = str(key)
    return (ACTION_NAME, key_name) if 0 < len(key_name) <= MAX_KEY_LENGTH else None


def update(held_keys: Iterable[str]) -> bool:
    """Applies or restores the narrow hold-action mute; False while no live input list exists."""
    mappings = _mappings()
    if mappings is None:
        return False
    held = _held(held_keys)
    count = len(mappings)
    if count > MAX_MAPPINGS:
        report.error_once("slam_hold:mappings", f"input mappings limited to {MAX_MAPPINGS}")
    occurrences: dict[str, int] = {}
    seen: set[tuple[str, int]] = set()
    for index in range(min(count, MAX_MAPPINGS)):
        entry = mappings[index]
        names = _names(entry)
        if names is None:
            continue
        _, key = names
        occurrence = occurrences.get(key, 0)
        occurrences[key] = occurrence + 1
        token = (key, occurrence)
        seen.add(token)
        ignored = bool(entry.bShouldBeIgnored)
        if key in held:
            if token not in _originals:
                if len(_originals) >= MAX_HELD_KEYS:
                    report.error_once("slam_hold:states", f"native hold states limited to {MAX_HELD_KEYS}")
                    continue
                _originals[token] = ignored
            if not ignored:
                entry.bShouldBeIgnored = True
                mappings[index] = entry
        elif token in _originals:
            original = _originals.pop(token)
            if ignored != original:
                entry.bShouldBeIgnored = original
                mappings[index] = entry
    for token in tuple(_originals):
        if token[0] not in held and token not in seen:
            _originals.pop(token)
    return True


def release() -> None:
    """Restores live mappings when possible and always forgets saved ownership."""
    try:
        update(())
    finally:
        _originals.clear()
