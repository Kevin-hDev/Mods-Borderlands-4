"""The automatic camera distance: under a low ceiling or in a narrow passage the camera comes to the close distance on
its own, and goes back to the chosen one once out (Kevin, 2026-10-11,
docs/third_person_fov/camera/2026-10-07-idees-troisieme-personne.md, list 2 n° 2).

Already at the close distance, nothing changes. Two delays and a margin keep a doorway or a rough wall from moving the
camera back and forth; the distance key always wins.
"""

# Thresholds (cm) of the first trial, kept: Kevin, 2026-10-11, « c'est parfait ça fonctionne super bien » (rooms
# measured in docs/third_person_fov/camera/releves/2026-10-11-distance-auto/sdk-essai-1.log).
CEILING_CM = 150.0
WIDTH_CM = 300.0
# Once close, the place must be this much roomier to count as left.
MARGIN_CM = 25.0
# Cramped this long to come in; roomy this long to go back, so walking through a door moves nothing.
ENTER_S = 0.3
LEAVE_S = 1.0
# An automatic move glides gentler than the key's (camera_distance.SECONDS).
GLIDE_S = 0.5


def cramped(reading, close: bool) -> bool:
    """reading: camera_distance_room.Reading; close: the close distance is shown, so leaving needs the margin."""
    margin = MARGIN_CM if close else 0.0
    return reading.ceiling < CEILING_CM + margin or reading.narrowest < WIDTH_CM + margin


class AutoDistance:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.close = False
        # After the player's key in a cramped place, wait until out of it before acting again: the key is not undone a
        # moment later, as the automatic shoulder does after the shoulder key.
        self.waiting = False
        self.cramped = False
        self.cramped_s = self.roomy_s = 0.0

    def player_key(self) -> None:
        self.close = False
        self.waiting = self.cramped
        self.cramped_s = self.roomy_s = 0.0

    @property
    def holding(self) -> bool:
        """Close shown or waiting: leaving the place is what matters now."""
        return self.close or self.waiting

    def step(self, cramped: bool | None, allowed: bool, seconds: float) -> bool:
        """Whether the close distance is shown. cramped is None when the room is not read; while not allowed (aiming,
        already at the close distance) the camera holds."""
        if not allowed or cramped is None:
            self.cramped_s = self.roomy_s = 0.0
            return self.close
        self.cramped = cramped
        if self.holding:
            self.roomy_s = 0.0 if cramped else self.roomy_s + seconds
            if self.roomy_s >= LEAVE_S:
                self.close = self.waiting = False
                self.roomy_s = 0.0
            return self.close
        self.cramped_s = self.cramped_s + seconds if cramped else 0.0
        if self.cramped_s >= ENTER_S:
            self.close, self.cramped_s = True, 0.0
        return self.close
