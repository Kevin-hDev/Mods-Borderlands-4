"""What the dynamic camera reads from the player each frame; any field the game has not built yet means no sample.

One reading for its three effects: the speed FOV, the framing by action and the camera motion.
"""

import math
import re
from dataclasses import dataclass
from typing import Any

SLIDE_MOVE = "Move_Slide"


@dataclass(frozen=True)
class Sample:
    sprinting: bool
    sliding: bool
    in_air: bool
    driven: bool
    # Three axes: the grapple's pull and a dive are speed the player feels.
    speed: float
    aiming: bool
    crouched: bool = False
    velocity: tuple[float, float, float] = (0.0, 0.0, 0.0)

    @property
    def flat_speed(self) -> float:
        return math.hypot(self.velocity[0], self.velocity[1])


def read(pc: Any) -> Sample | None:
    character = getattr(pc, "OakCharacter", None) if pc is not None else None
    if character is None:
        return None
    try:
        movement = character.CharacterMovement
        velocity = tuple(float(value) for value in (movement.Velocity.X, movement.Velocity.Y, movement.Velocity.Z))
        if not all(math.isfinite(value) for value in velocity):
            velocity = (0.0, 0.0, 0.0)
        mode = re.search(r"MOVE_\w+", repr(movement.MovementMode))
        # A slide, a dash or a ground slam, asked of the game: its network copy keeps a ground slam after landing
        # (verified in game, 2026-09-18). The copy names the move only while the game says one is running.
        driven = bool(movement.IsPerformingControlledMove())
        move = movement.ControlledMoveReplicationData.ControlledMove if driven else None
        zoom = character.ZoomState
        aiming = bool(zoom.bWantsToZoom) or getattr(zoom.State, "name", str(zoom.State)) != "NotZoomed"
        # The grapple and every jump put the player in Falling.
        return Sample(bool(movement.bIsSprinting), move is not None and str(getattr(move, "Name", "")) == SLIDE_MOVE,
                      mode is not None and mode.group(0) == "MOVE_Falling", driven,
                      math.sqrt(sum(value * value for value in velocity)), aiming,
                      bool(getattr(character, "bIsCrouched", False)), velocity)
    except (AttributeError, TypeError, ValueError):
        return None
