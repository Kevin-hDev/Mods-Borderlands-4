"""What the dynamic camera reads from the player each frame; any field the game has not built yet means no sample.

One reading for its three effects: the speed FOV, the framing by action and the camera motion.
"""

import math
import re
from dataclasses import dataclass
from typing import Any

SLIDE_MOVE = "Move_Slide"
_NO_NAME = object()


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
    # The aim button held: `aiming` also covers the game's zoom-out after it, which the FOV waits for.
    aim_held: bool = False

    @property
    def flat_speed(self) -> float:
        return math.hypot(self.velocity[0], self.velocity[1])


def _mode_name(mode: Any) -> str | None:
    # The game's enum carries its name; its text and a search are only the fallback.
    name = getattr(mode, "name", None)
    if isinstance(name, str) and name.startswith("MOVE_"):
        return name
    found = re.search(r"MOVE_\w+", repr(mode))
    return found.group(0) if found else None


def read(pc: Any) -> Sample | None:
    character = getattr(pc, "OakCharacter", None) if pc is not None else None
    if character is None:
        return None
    try:
        # Each field read once: this runs once or twice a frame (2026-10-24).
        movement = character.CharacterMovement
        speed = movement.Velocity
        velocity = (float(speed.X), float(speed.Y), float(speed.Z))
        if not all(math.isfinite(value) for value in velocity):
            velocity = (0.0, 0.0, 0.0)
        mode = _mode_name(movement.MovementMode)
        # A slide, a dash or a ground slam, asked of the game: its network copy keeps a ground slam after landing
        # (verified in game, 2026-09-18). The copy names the move only while the game says one is running.
        driven = bool(movement.IsPerformingControlledMove())
        move = movement.ControlledMoveReplicationData.ControlledMove if driven else None
        zoom = character.ZoomState
        aim_held = bool(zoom.bWantsToZoom)
        aiming = aim_held
        if not aiming:
            state = zoom.State
            name = getattr(state, "name", _NO_NAME)
            aiming = (str(state) if name is _NO_NAME else name) != "NotZoomed"
        # The grapple and every jump put the player in Falling.
        return Sample(bool(movement.bIsSprinting), move is not None and str(getattr(move, "Name", "")) == SLIDE_MOVE,
                      mode == "MOVE_Falling", driven,
                      math.sqrt(sum(value * value for value in velocity)), aiming,
                      bool(getattr(character, "bIsCrouched", False)), velocity, aim_held)
    except (AttributeError, TypeError, ValueError):
        return None
