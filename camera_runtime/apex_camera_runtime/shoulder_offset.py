"""The shoulder's share of the third-person camera offset, given to the game (Kevin, 2026-10-08).

camera_offset.py adds it to the game's camera offset, which the game applies before its own collision: one system
places the camera. The native camera used to add the shoulder after the game's collision, and the mod's wall check
then cut it again; the two disagreed and the camera jumped twice behind the same pole
(docs/third_person_fov/camera/enquetes/2026-10-08-sauts-camera-collisions.md, third trial: "c'est pas parfait mais
c'est mieux").

It keeps the native camera's transitions (offset_blend.h, offset_transition.cpp): a side swap glides over the
shoulder's transition time; aiming and the vehicle take the shoulder away and give it back at once; climbing, Orbit and
the third-person toggle glide it out and back over their own time, in the modes their permission names. The framing's
spacing and height grow with the shoulder as the native framing measured them, from the hunter's sideways distance
(framing_math.cpp).
"""

import math
import time

from .constants import CLIMB_MODE, THIRD_PERSON_MODE, THIRD_PERSON_UP
from .framing_catalog import GROUPS
from .generated_limits import SHOULDER_MAX_OFFSET
from .transition_catalog import SHOULDER_SECONDS_MAX

NS = 1_000_000_000
SPACING, HEIGHT = (next(group for group in GROUPS if group.key == key) for key in ("horizontal", "height"))


def framing_share(settings) -> tuple:
    """The framing's spacing and height as fractions; 0 for a mod without the framing or an unreadable choice, which
    the framing itself refuses to render too (framing_session.py)."""
    read = getattr(settings, "framing_values", None)
    snapshot = read() if callable(read) else None
    if type(snapshot) is not tuple or len(snapshot) != len(GROUPS):
        return 0.0, 0.0
    rows = dict(zip((group.key for group in GROUPS), snapshot))
    values = tuple(rows[group.key][0] if type(rows[group.key]) is tuple and rows[group.key] else None
                   for group in (SPACING, HEIGHT))
    return tuple(value / 100.0 if group.valid(value) else 0.0 for group, value in zip((SPACING, HEIGHT), values))


def _seconds(value) -> float:
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= SHOULDER_SECONDS_MAX:
        raise ValueError("Invalid camera transition duration")
    return float(value)


class ShoulderOffset:
    def __init__(self, clock=time.perf_counter_ns) -> None:
        self.clock = clock
        self.reset()

    def reset(self) -> None:
        # The signed shoulder (cm, right positive), 0 until a side is given.
        self.right = 0.0
        self.seconds = 0.0
        self.suspended = False
        self.climbing = False
        self.permission = None
        # The glide: where it started (sideways cm, share of the lift), when, for how long, and whether it is a swap.
        self._start = (0.0, 0.0)
        self._started = 0
        self._duration = 0.0
        self._swap = False
        # What the game was last given (sideways, up, clock), for the room the automatic shoulder reads.
        self.applied = None

    def show(self, right) -> bool:
        if (isinstance(right, bool) or not isinstance(right, (int, float)) or not math.isfinite(right)
                or abs(right) > SHOULDER_MAX_OFFSET):
            return False
        if right != self.right:
            # The first side, and a side given while suspended, stand at once.
            instant = self.suspended or self.right == 0.0
            self._begin(0.0 if instant else self.seconds, swap=not self.suspended)
            self.right = float(right)
        return True

    def transition_duration(self, seconds) -> None:
        seconds = _seconds(seconds)
        if seconds != self.seconds:
            self.seconds = seconds
            if not seconds and self._swap:
                self._begin(0.0, swap=True)

    def suspend(self, suspended: bool, seconds: float = 0.0, permission=None, climbing: bool = False) -> None:
        """Without seconds (aiming, the vehicle) the shoulder goes or comes back at once, ending any glide; with seconds
        (climbing, Orbit, the toggle) it glides when the state changes."""
        if type(suspended) is not bool:
            raise ValueError("Invalid camera offset suspension")
        seconds = _seconds(seconds)
        if not seconds or suspended != self.suspended:
            self._begin(seconds, swap=False)
            self.suspended = suspended
        self.permission = permission if seconds else None
        self.climbing = climbing

    def transition_active(self) -> bool:
        """A glide of climbing, Orbit or the toggle is under way; a side swap is not one."""
        return not self._swap and self._duration > 0 and self.clock() - self._started < self._duration * NS

    def allows(self, manager, actor) -> bool:
        """The modes the shoulder shows in: ThirdPerson, climbing's own mode while climbing, and while a glide's
        permission answers, the modes it names."""
        if self.permission is not None:
            if not self.transition_active():
                self.permission = None
            else:
                permitted = self.permission(manager, actor)
                if permitted is not None:
                    return permitted is True
        mode = str(manager.GetActorCameraMode(actor))
        return mode == THIRD_PERSON_MODE or (self.climbing and mode == CLIMB_MODE)

    def place(self, spacing: float, height: float) -> tuple:
        """The shoulder's share of the camera offset now, sideways and up (cm, camera axes); spacing and height are
        the framing's, fractions of the hunter's sideways distance."""
        now = self.clock()
        lateral, lift = self._value(now)
        side = lateral * (1.0 + spacing)
        up = lift * THIRD_PERSON_UP + height * abs(lateral)
        self.applied = (side, up, now)
        return side, up

    def withhold(self) -> None:
        self.applied = None

    def _goal(self) -> tuple:
        return (0.0, 0.0) if self.suspended else (self.right, 1.0)

    def _value(self, now: int) -> tuple:
        goal = self._goal()
        if self._duration <= 0:
            return goal
        share = min(max((now - self._started) / (self._duration * NS), 0.0), 1.0)
        eased = share * share * (3.0 - 2.0 * share)
        return tuple(start + (end - start) * eased for start, end in zip(self._start, goal))

    def _begin(self, seconds: float, swap: bool) -> None:
        now = self.clock()
        self._start = self._value(now)
        self._started, self._duration, self._swap = now, seconds, swap
