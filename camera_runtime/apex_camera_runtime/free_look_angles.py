"""Free Look at the wheel: the camera's own turn while the vehicle keeps its direction, free of the game.

Each frame the game rebuilds the view from the turned camera, then adds the mouse; the turn is taken back out of
the view and kept for the camera alone. Adding it a second time made the camera run away (2026-10-06, trial 2).
"""

PITCH_LIMIT = 80.0


def turn(angle: float) -> float:
    """The same direction between -180 and 180: the game keeps pitch as 0 to 360 (350 for -10)."""
    return (float(angle) + 180.0) % 360.0 - 180.0


class Look:
    def __init__(self, pitch: float, yaw: float) -> None:
        self.anchor = (turn(pitch), turn(yaw))
        self.pitch = self.yaw = 0.0

    def absorb(self, pitch: float, yaw: float) -> tuple:
        """The camera goes where the game turned the view; gives the view to put back."""
        anchor_pitch, anchor_yaw = self.anchor
        self.yaw = turn(turn(yaw) - anchor_yaw)
        self.pitch = max(-PITCH_LIMIT, min(PITCH_LIMIT, turn(pitch))) - anchor_pitch
        return self.anchor
