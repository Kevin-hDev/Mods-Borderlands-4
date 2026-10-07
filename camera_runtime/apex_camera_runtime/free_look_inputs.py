"""Free Look reads the player's own movement keys from the game's key list, free of the game for its tests.

The game maps its four keyboard movement keys to one action, Action_Move, told apart by their modifiers (journal
releves/apex_inputs_2026-09-16.log, Kevin's AZERTY game): right has none, left is negated, forward is swizzled,
back is swizzled and negated. Reading them there follows any layout and any key the player chose (decision of
2026-09-26 in the camera drone investigation). The stick is read as Gamepad_LeftX and the brake trigger as
Gamepad_LeftTriggerAxis, as the camera drone probe read them (verified in game, 2026-09-26).
"""

from typing import Any, Callable, NamedTuple

from .free_look_run import braking, lateral

MOVE_ACTION = "Action_Move"
NEGATE, SWIZZLE = "InputModifierNegate", "InputModifierSwizzleAxis"
STICK_X, TRIGGER = "Gamepad_LeftX", "Gamepad_LeftTriggerAxis"
# Bounded: the game lists about a hundred mappings; anything far beyond is not its list.
MAX_MAPPINGS = 512


class MoveKeys(NamedTuple):
    right: tuple
    left: tuple
    back: tuple


def _class_name(modifier: Any) -> str:
    return str(getattr(getattr(modifier, "Class", None), "Name", ""))


def move_keys(mappings: Any) -> MoveKeys:
    right, left, back = [], [], []
    for index, mapping in enumerate(mappings):
        if index >= MAX_MAPPINGS:
            break
        action = getattr(mapping, "Action", None)
        key = str(getattr(getattr(mapping, "Key", None), "KeyName", ""))
        if (action is None or str(action.Name) != MOVE_ACTION or not key or key.startswith("Gamepad_")
                or getattr(mapping, "bShouldBeIgnored", False) is True):
            continue
        names = {_class_name(modifier) for modifier in (getattr(mapping, "Modifiers", None) or ())}
        swizzled, negated = SWIZZLE in names, NEGATE in names
        if swizzled and negated:
            back.append(key)
        elif negated:
            left.append(key)
        elif not swizzled:
            right.append(key)
    return MoveKeys(tuple(right), tuple(left), tuple(back))


def _most(value: Callable[[str], float], keys: tuple) -> float:
    return max((value(key) for key in keys), default=0.0)


def side(value: Callable[[str], float], keys: MoveKeys) -> float:
    """Left and right, keyboard and stick together; value(key name) is the game's analog state of that key."""
    return lateral(_most(value, keys.right), _most(value, keys.left), value(STICK_X))


def brakes(value: Callable[[str], float], keys: MoveKeys) -> bool:
    return braking(_most(value, keys.back), value(TRIGGER))
