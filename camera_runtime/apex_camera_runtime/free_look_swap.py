"""Free Look in first person: the game's third person is laid over it for the hold, then taken off.

Kevin, 2026-10-06: in first person the hunter's shoulder hides half the screen once the camera turns away, and
seeing the hunter is more natural; on 2026-10-07 he chose the game's own third person over the mods' framing. His
Free Look has no animation, so the switch is instant, the way the camera mods enter first-person aiming (aiming.py:
blend 0, teleport). The camera mods' controller is off in first person, so while the layer is there the game's own
requests for a first-person camera are refused here: a slide asks for "Slide" then "Default", which took the layer
off (trial 15). Aiming goes through, as in transitions.py. Taking off a layer the game already removed changes
nothing (trial 15). Verified in game with the probe, trials 11 and 16.
"""

from typing import Any

from .transitions import ON_FOOT_MODES, REQUESTS

FIRST_PERSON = "Default"
THIRD_PERSON = "ThirdPerson"
TRANSITION = "Default"
BLEND_S = 0.0
TELEPORT = True
IDENTIFIER = "apex_camera_runtime:free_look_guard"


def lay(pc: Any) -> Any:
    """The actor third person was laid on."""
    actor = pc.OakCharacter
    pc.PlayerCameraManager.PushActorCameraMode(actor, THIRD_PERSON, TRANSITION, BLEND_S, TELEPORT)
    return actor


def take_off(manager: Any, actor: Any) -> None:
    manager.PopActorCameraMode(actor, THIRD_PERSON, TRANSITION, BLEND_S, TELEPORT)


def same(first: Any, second: Any) -> bool:
    try:
        return int(first._get_address()) == int(second._get_address())
    except (AttributeError, TypeError, ValueError):
        return first is second


def aiming(pc: Any) -> bool:
    try:
        return bool(pc.OakCharacter.ZoomState.bWantsToZoom)
    except Exception:
        return False


class Guard:
    """Refuses the game's first-person requests for one controller while third person is laid."""

    def __init__(self, hooks: Any) -> None:
        self.hooks = hooks
        self.pc = None

    def _callback(self, field: str):
        def on_request(obj: Any, args: Any, _ret: Any, _func: Any) -> Any:
            if (self.pc is None or not same(obj, self.pc) or str(getattr(args, field)) not in ON_FOOT_MODES
                    or aiming(self.pc)):
                return None
            return self.hooks.Block
        return on_request

    def install(self, pc: Any) -> None:
        self.pc = pc
        for path, names in REQUESTS.items():
            if not self.hooks.has_hook(path, self.hooks.Type.PRE, IDENTIFIER):
                self.hooks.add_hook(path, self.hooks.Type.PRE, IDENTIFIER, self._callback(names[0]))

    def remove(self) -> None:
        self.pc = None
        for path in REQUESTS:
            if self.hooks.has_hook(path, self.hooks.Type.PRE, IDENTIFIER):
                self.hooks.remove_hook(path, self.hooks.Type.PRE, IDENTIFIER)
