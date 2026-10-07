"""When a wall takes the shoulder's room, show the other shoulder, then come back (Kevin, 2026-10-07).

docs/third_person_fov/camera/2026-10-07-idees-troisieme-personne.md, idea 1. The saved shoulder never changes: this
only chooses which side is shown. Two thresholds and two delays keep a rough wall from making the camera swing.
"""

from typing import NamedTuple

# Share of the shoulder's offset left free on the shown side below which it counts as blocked.
BLOCKED = 0.5
# Share the other side must keep free to be worth going to, or the chosen side to come back to.
CLEAR = 0.9
# The default delays, set by the player (shoulder_auto_options.py). Kevin, 2026-10-07 second trial: a 1 s return felt
# slow ("between one and two seconds").
SWAP_S = 0.15
RETURN_S = 0.3


class Values(NamedTuple):
    """The player's choices (shoulder_auto_options.py)."""
    enabled: bool
    swap_s: float
    return_s: float


class AutoShoulder:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        # The side shown instead of the chosen one, or None while the chosen side is shown.
        self.override: bool | None = None
        # After the player's own switch, wait for the chosen side to clear before acting again.
        self.waiting = False
        self.blocked_s = self.clear_s = 0.0

    def shown(self, chosen_left: bool) -> bool:
        return chosen_left if self.override is None else self.override

    def player_switch(self) -> bool:
        """The shoulder key during a swap brings the chosen shoulder back; False when nothing was swapped."""
        if self.override is None:
            return False
        self.reset()
        self.waiting = True
        return True

    def step(self, chosen_left: bool, shown_free: float | None, other_free: float | None,
             allowed: bool, seconds: float, swap_s: float = SWAP_S, return_s: float = RETURN_S) -> bool:
        """Return the side to show. Free shares are None when not measured this frame."""
        if self.override == chosen_left:
            self.override = None
        if not allowed or shown_free is None:
            # Aiming or no reading: hold the side shown, restart the delays.
            self.blocked_s = self.clear_s = 0.0
            return self.shown(chosen_left)
        if self.override is None:
            self.clear_s = 0.0
            if self.waiting:
                self.waiting = shown_free < CLEAR
            elif shown_free < BLOCKED and other_free is not None and other_free >= CLEAR:
                self.blocked_s += seconds
                if self.blocked_s >= swap_s:
                    self.override, self.blocked_s = not chosen_left, 0.0
            else:
                self.blocked_s = 0.0
        else:
            self.blocked_s = 0.0
            if other_free is not None and other_free >= CLEAR:
                self.clear_s += seconds
                if self.clear_s >= return_s:
                    self.override, self.clear_s = None, 0.0
            else:
                self.clear_s = 0.0
        return self.shown(chosen_left)
