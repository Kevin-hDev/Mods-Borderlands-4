"""Presses for the player, for one input frame, the game's action a kept grapple key carries: the punch a tap gives back
in hold mode (key_hold.py).

Injecting Action_Melee through Enhanced Input, as Apex Movement presses Croix (apex_movement/jump_press.py), punched 2
times out of 2, 13 to 17 ms after the call, the same punch as R3's; the press does not go through the SDK's key binds,
so this mod never sees it as a new press (verified in game on 2026-10-06,
docs/investigations/apex_grapple/commandes/2026-10-06-coup-de-poing-par-le-mod.md). The function is declared on the
interface, not on the subsystem's class, so it is bound to the subsystem by hand. Looked up once per controller: the
lookup scans the game's objects, too slow for every press.
"""

from itertools import islice
from typing import Any

import unrealsdk
from unrealsdk.unreal import BoundFunction

from . import game, input_list

SUBSYSTEM = "/Script/EnhancedInput.EnhancedInputLocalPlayerSubsystem"
INTERFACE = "EnhancedInputSubsystemInterface"
INJECT = "InjectInputVectorForAction"
# Bounded: Apex Movement found two subsystems, one per local player and one spare.
MAX_SUBSYSTEMS = 16

_controller: Any = None
_inject: tuple[Any, Any] | None = None


def press(key: str) -> list[str]:
    """Presses the grapple actions this key carries in the game's list, and names them; none for a key of the player's
    own, which the game gives no grapple action to."""
    pc = game.controller()
    if pc is None:
        return []
    if pc != _controller:
        _look_up(pc)
    if _inject is None:
        return []
    mappings = game.input_mappings()
    wanted = input_list.grapple_actions(mappings)
    actions = {str(mapping.Action.Name): mapping.Action for mapping in mappings
               if mapping.Action is not None and str(mapping.Key.KeyName) == key and str(mapping.Action.Name) in wanted}
    inject, value = _inject
    for action in actions.values():
        inject(Action=action, Value=value, Modifiers=[], Triggers=[])
    return sorted(actions)


def _look_up(pc: Any) -> None:
    global _controller, _inject
    _controller, _inject = pc, None
    subsystem = next((found for found in islice(unrealsdk.find_all(SUBSYSTEM, exact=False), MAX_SUBSYSTEMS)
                      if found.Outer == pc.Player), None)
    if subsystem is None:
        return
    function = unrealsdk.find_class(INTERFACE)._find(INJECT)
    _inject = (BoundFunction(function, subsystem), unrealsdk.make_struct("Vector", X=1.0, Y=0.0, Z=0.0))


def forget() -> None:
    global _controller, _inject
    _controller = _inject = None
