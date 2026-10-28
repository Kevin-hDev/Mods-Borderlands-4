"""Fits the heirloom in the hand: its size, its turn and the point of it held in the hand, as the chosen heirloom's hold
sets them (heirloom_catalog.py, from its heirloom.json); the player sets its size in the menu, a share of that
hold's, from the next weapon change.

Why, 2026-09-24 (cosmetics/heirloom/docs/enquetes/2026-09-23-modele-heirloom.md): Kevin chose, on an image drawn
outside the game, the knife held as Wraith holds her kunai, by the handle. Seen in game, he set its size to 62 %,
found the blade pointing at him, then, with the pose AS_UA_Idle_heirloom_droit, the index finger through the guard
and the blade a little high. In game, Kevin tried the held point at 0, 4, 5 and 6 cm on the knife's axis, and kept 6
(2026-09-24: "c'est parfait"). Size and turn apply about the held point: turned about the model's own origin, 33 cm
from the wrist in the game's pose, the knife left the hand (Kevin, 2026-09-24). Why a held point off the model's
axis, 2026-09-28: the axe is held in a full fist, right under its head, its grip point measured on the fist
(axe/heirloom.json, "hold"), tried in game through a trial command (sondes/apex_painted_trial.py, gone since) and
validated (2026-09-29).

The size keeps the anchor's reversed Y: the game hangs a right-hand object as the mirror of a left-hand one, and the
held point is mirrored with it.
"""

from dataclasses import dataclass
from typing import Any, Callable

import unrealsdk

Say = Callable[[str], None]
MIRRORED_Y = -1.0
MATH_LIBRARY = "KismetMathLibrary"


@dataclass
class Fit:
    size: float
    pitch: float
    yaw: float
    roll: float
    # The point of the model held on the hand's anchor, in cm of the model's own size, in its own axes.
    grip: tuple[float, float, float]

    @classmethod
    def of(cls, hold: dict[str, Any], percent: float = 100.0) -> "Fit":
        """The hold of an heirloom (heirloom_catalog.py), at `percent` of its size."""
        return cls(size=hold["size"] * percent / 100.0, pitch=hold["pitch"], yaw=hold["yaw"], roll=hold["roll"],
                   grip=tuple(float(v) for v in hold["grip"]))

    def shown(self) -> str:
        return (f"size {self.size:g} %, turn pitch {self.pitch:g}, yaw {self.yaw:g}, roll {self.roll:g} degrees, "
                f"held at {', '.join(f'{v:g}' for v in self.grip)} cm")


def apply(component: Any, fit: Fit, say: Say) -> None:
    scale = fit.size / 100.0
    make = unrealsdk.make_struct
    try:
        turn = make("Rotator", Pitch=fit.pitch, Yaw=fit.yaw, Roll=fit.roll)
        # The held point, mirrored, scaled and turned as the component will be, is moved back onto the anchor. The
        # engine turns it, so the turn is the component's own.
        x, y, z = fit.grip
        held = unrealsdk.find_class(MATH_LIBRARY).ClassDefaultObject.GreaterGreater_VectorRotator(
            make("Vector", X=scale * x, Y=scale * MIRRORED_Y * y, Z=scale * z), turn)
        component.SetRelativeScale3D(make("Vector", X=scale, Y=scale * MIRRORED_Y, Z=scale))
        component.K2_SetRelativeRotation(turn, False, make("HitResult"), False)
        component.K2_SetRelativeLocation(make("Vector", X=-held.X, Y=-held.Y, Z=-held.Z), False, make("HitResult"),
                                         False)
        say(f"fit: {fit.shown()}")
    except Exception as exc:
        say(f"the fit could not be applied: {exc!r}")
