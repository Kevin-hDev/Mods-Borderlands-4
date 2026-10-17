"""Another player's grapple with the classic look: the game's own rope effect from that player's left hand to the
anchor, in that player's colour (look_code.py).

The player's own classic rope (beam.py) is put in the world free, ends written in its own axes (rope_pose.py,
rope_ends.py); this one is put the same way. Its hand is the body's left-hand bone the grapple gun's pistol hangs on
(look_assets.PIECES), seen on every hunter from outside. The effect lives in the world, not on the character: it is
removed at release, whatever became of the character.
"""

from typing import Any

import unrealsdk
from unrealsdk.unreal import WeakPointer

from . import beam_cleanup, beam_colour, game, look_assets, rope_ends, rope_lifetime, rope_light, rope_pose

LIBRARY = "NiagaraFunctionLibrary"
HAND_BONE = look_assets.PIECES["pistol_body"]["bone"]

# The two ends' names, found once on the first rope drawn: the effect is the same for every player.
_ends: dict[str, str | None] = {}


def _library() -> Any:
    return unrealsdk.find_class(LIBRARY).ClassDefaultObject


def hand(character: Any) -> tuple[float, float, float]:
    spot = character.Mesh.GetSocketLocation(HAND_BONE)
    return float(spot.X), float(spot.Y), float(spot.Z)


class BeamGrapple:
    def __init__(self, character: Any, look: Any) -> None:
        self.pointer = WeakPointer(character)
        self.look = look
        self.component: Any = None
        self.anchor = (0.0, 0.0, 0.0)

    def character(self) -> Any:
        return self.pointer()

    def busy(self) -> bool:
        return self.component is not None

    def start(self, anchor: tuple, flight_s: float, now_ns: int) -> None:
        self.release(now_ns)
        character = self.pointer()
        system = game.beam_effect()
        if character is None or system is None:
            return
        rope_ends.read_names(system)
        here = hand(character)
        pitch, yaw = rope_pose.facing(here, anchor)
        made = _library().SpawnSystemAtLocation(
            character, system, rope_ends.vector(here), unrealsdk.make_struct("Rotator", Pitch=pitch, Yaw=yaw, Roll=0.0),
            unrealsdk.make_struct("Vector", X=1.0, Y=1.0, Z=1.0), False, False, 0, True)
        if isinstance(made, tuple):
            made = made[0] if made else None
        if made is None:
            raise RuntimeError("the game handed back no rope effect")
        self.component, self.anchor = made, tuple(anchor)
        beam_colour.paint(made, self.look.game_rope_colour)
        rope_lifetime.configure(made, system)
        self._follow(here)
        rope_light.switch_on(made)

    def _follow(self, here: tuple) -> None:
        library = _library()
        target = rope_pose.follow(self.component, here, self.anchor)
        if "far" not in _ends:
            _ends["far"] = rope_ends.find(self.component, library, rope_ends.TARGET_WORDS, target, "far end")
            _ends["near"] = rope_ends.find(self.component, library, rope_ends.SOURCE_WORDS, rope_pose.ORIGIN,
                                           "near end")
        if _ends["far"] is not None:
            rope_ends.write(self.component, library, _ends["far"], target)
        if _ends["near"] is not None:
            rope_ends.write(self.component, library, _ends["near"], rope_pose.ORIGIN)

    def tick(self, _now_ns: int) -> None:
        character = self.pointer()
        if self.component is not None and character is not None:
            self._follow(hand(character))

    def release(self, _now_ns: int) -> None:
        made, self.component = self.component, None
        if made is None:
            return
        made.bAutoDestroy = True
        made.Deactivate()
        # The player's own beam's ways of removing it, the reflected one first (beam_cleanup.py).
        for name in beam_cleanup.DESTROY_NAMES:
            remove = getattr(made, name, None)
            if remove is None:
                continue
            if name == "K2_DestroyComponent":
                owner = made.GetOwner()
                remove(owner if owner is not None else made)
            else:
                remove()
            return

    def drop(self) -> None:
        self.release(0)


def reset() -> None:
    _ends.clear()
