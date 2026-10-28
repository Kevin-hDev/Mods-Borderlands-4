"""Presses Croix for the player for one input frame, through Enhanced Input, as the controller does.

Sessions F to H (2026-09-17): the game mantles over a ledge only when Croix is held, and it answers the input action
Action_Jump_HoldToGlide, not character.bPressedJump (0 mantles in 6 climbs). Injecting that action with
EnhancedInputSubsystemInterface.InjectInputVectorForAction, bound to the player's EnhancedInputLocalPlayerSubsystem,
mantled 6 climbs out of 6, one frame being enough, with no double jump. The function is declared on the interface, so
it is not found on the subsystem's class and is bound to the subsystem by hand. Looked up once per controller: the
lookup scans the game's objects, too slow for every frame.
"""

from itertools import islice
from typing import Any

import unrealsdk
from unrealsdk.unreal import BoundFunction

from . import game

JUMP_ACTION = "Action_Jump_HoldToGlide"
SUBSYSTEM = "/Script/EnhancedInput.EnhancedInputLocalPlayerSubsystem"
INTERFACE = "EnhancedInputSubsystemInterface"
INJECT = "InjectInputVectorForAction"
# Bounded: session H found two subsystems, one per local player and one spare.
MAX_SUBSYSTEMS = 16

_controller: Any = None
_press: tuple[Any, Any, Any] | None = None


def press() -> bool:
    """Presses Croix for the next input frame; False when the game offers no way to, looked up again next controller."""
    pc = game.controller()
    if pc is None:
        return False
    if pc != _controller:
        _look_up(pc)
    if _press is None:
        return False
    inject, action, value = _press
    inject(Action=action, Value=value, Modifiers=[], Triggers=[])
    return True


def _look_up(pc: Any) -> None:
    global _controller, _press
    _controller, _press = pc, None
    action = next((mapping.Action for mapping in game.input_mappings()
                   if mapping.Action is not None and str(mapping.Action.Name) == JUMP_ACTION), None)
    subsystem = next((found for found in islice(unrealsdk.find_all(SUBSYSTEM, exact=False), MAX_SUBSYSTEMS)
                      if found.Outer == pc.Player), None)
    if action is None or subsystem is None:
        return
    function = unrealsdk.find_class(INTERFACE)._find(INJECT)
    _press = (BoundFunction(function, subsystem), action, unrealsdk.make_struct("Vector", X=1.0, Y=0.0, Z=0.0))


def forget() -> None:
    global _controller, _press
    _controller = _press = None
