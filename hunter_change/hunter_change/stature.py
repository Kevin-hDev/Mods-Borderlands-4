"""The played character's size: the capsule, eye heights and body height of the hunter whose look it wears, so that
the view and the crosshair stand at that hunter's shoulder as in its own game (Kevin, 2026-10-07: "exactly the same
render", for the six). The played hunter so takes the worn one's bulk too, which Kevin accepts.

Verified in game on Rafa dressed as Amon (2026-10-08, docs/reverse-and-change-hunters/enquetes/
2026-10-07-taille-du-chasseur-porte.md): the game puts the played hunter's own size back each time the character
stands up from a crouch or a slide, and Unreal's crouch events never reach the SDK; so keep() looks at the size at
each frame and gives the worn one again, standing, in the same frame. While crouched the game's own crouch is left
alone. The crouched half height is set before the eye heights: Unreal's SetCrouchedHalfHeight works the crouched eye
height out again from the class's defaults (the 69.5 written for Amon read 48.4 when it was set last). A game that
would put its size back at every frame cannot lift the character away: past MAX_PER_SECOND gives within a second,
the size is no longer kept for that character, said once.
"""

import time
import types
from typing import Any

import unrealsdk
from unrealsdk.unreal import WeakPointer

from . import report
from .hunters import CROUCHED_HALF, RADIUS, Hunter

STEP_S = 1 / 60
OFF = 0.5
MAX_PER_SECOND = 3

_STATE = types.SimpleNamespace(character=None, hunter=None, last=0.0, recent=[], stopped=False)


def _vector(source: Any, z: float) -> Any:
    return unrealsdk.make_struct("Vector", X=float(source.X), Y=float(source.Y), Z=z)


def _give(character: Any, hunter: Hunter) -> bool:
    size = hunter.stature
    lift = size.half - float(character.CapsuleComponent.CapsuleHalfHeight)
    steps = (
        ("capsule", lambda: character.CapsuleComponent.SetCapsuleSize(RADIUS, size.half, True)),
        # Lifted by the half height gained, so that the feet stay on the ground.
        ("lift", lambda: character.K2_SetActorLocation(
            _vector(character.K2_GetActorLocation(), float(character.K2_GetActorLocation().Z) + lift), False,
            unrealsdk.make_struct("HitResult"), True)),
        ("body", lambda: character.Mesh.K2_SetRelativeLocation(
            _vector(character.Mesh.RelativeLocation, size.mesh_z), False, unrealsdk.make_struct("HitResult"), True)),
        ("crouched", lambda: character.CharacterMovement.SetCrouchedHalfHeight(CROUCHED_HALF)),
        ("eyes", lambda: (setattr(character, "BaseEyeHeight", size.eye),
                          setattr(character, "CrouchedEyeHeight", size.crouched_eye))),
    )
    for label, step in steps:
        try:
            step()
        except Exception as error:
            report.error_once(f"stature:{label}", f"{hunter.name}'s size was refused at the {label} step, the view "
                                                  f"may stand at another height: {error!r}")
            return False
    return True


def wear(character: Any, hunter: Hunter) -> bool:
    """`hunter`'s size on the character now, kept on it from then on (keep)."""
    _STATE.character, _STATE.hunter, _STATE.recent, _STATE.stopped = WeakPointer(character), hunter, [], False
    return _give(character, hunter)


def forget() -> None:
    """No size kept any more: a new wear() starts again."""
    _STATE.character, _STATE.hunter = None, None


def keep(character: Any, now: float | None = None) -> None:
    """At most once a frame: the size worn given again when the game has put the character's own back, standing."""
    now = time.perf_counter() if now is None else now
    held = _STATE.character() if _STATE.character is not None else None
    if _STATE.stopped or held is None or held != character or now - _STATE.last < STEP_S:
        return
    _STATE.last = now
    size = _STATE.hunter.stature
    if getattr(character, "bIsCrouched", False) or abs(float(character.CapsuleComponent.CapsuleHalfHeight)
                                                        - size.half) <= OFF:
        return
    _STATE.recent = [at for at in _STATE.recent if now - at < 1.0] + [now]
    if len(_STATE.recent) > MAX_PER_SECOND:
        _STATE.stopped = True
        report.error_once("stature:fight", f"the game keeps putting the character's own size back; "
                                           f"{_STATE.hunter.name}'s is no longer kept on this character")
        return
    _give(character, _STATE.hunter)
