"""The legs and the chest follow the body turned toward its run (body_facing.py).

Trial 2 (2026-10-09, docs/investigations/apex_movement/animation/2026-10-09-corps-gauche-droite.md) turned the body
on every side, but the game animated the legs for a body at most 75 degrees from the camera, and twisted the chest
back to the crosshair up to 177 degrees. Direction now gets the run seen from the turned body, and the chest's aim
offset fades past FULL_TWIST (trial 3, Kevin: « ok c'est parfait »).
"""

from typing import Any

# _1 drives the mech arms' auto-lock (AimO_AutoLock_MechArms), not the chest: left alone.
AIM_NODES = ("GbxAnimGraphNode_Rotation_AimOffset", "GbxAnimGraphNode_Rotation_AimOffset_2",
             "GbxAnimGraphNode_Rotation_AimOffset_3", "GbxAnimGraphNode_Rotation_AimOffset_4",
             "GbxAnimGraphNode_Rotation_AimOffset_5")
# Kevin found the left run good with the chest twisted 88 degrees to the crosshair: kept up to 90 degrees.
FULL_TWIST = 90.0
NO_TWIST = 135.0


def twist_alpha(offset: float) -> float:
    """How much of the game's chest twist to keep for a body `offset` degrees from the camera."""
    turn = abs(offset)
    if turn <= FULL_TWIST:
        return 1.0
    if turn >= NO_TWIST:
        return 0.0
    return (NO_TWIST - turn) / (NO_TWIST - FULL_TWIST)


class Pose:
    """Owns the chest nodes' intensities while the body is held; restore() gives the game's back."""

    def __init__(self) -> None:
        self.original: dict[str, float] | None = None

    def apply(self, anim: Any, offset: float, run_vs_body: float | None) -> None:
        if self.original is None:
            # Read when the hold starts, from what the game left there.
            self.original = {name: float(getattr(anim, name).ALPHA) for name in AIM_NODES}
        alpha = twist_alpha(offset)
        for name, original in self.original.items():
            getattr(anim, name).ALPHA = original * alpha
        if run_vs_body is not None:
            anim.Direction = run_vs_body

    def restore(self, anim: Any) -> None:
        original, self.original = self.original, None
        if original is None or anim is None:
            return
        for name, value in original.items():
            getattr(anim, name).ALPHA = value
