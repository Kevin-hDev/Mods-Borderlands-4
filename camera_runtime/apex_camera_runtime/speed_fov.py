"""Sprint widens the view (Kevin, 2026-10-06): the player's FOV plus a gain, smoothed in and out.

In Apex, Octane's stim adds 10 to the FOV; here a sprint or a slide starts it (Kevin added the slide without a sprint
after the second test). What follows keeps it: a jump, the grapple and any fall (the air), a slide or a dash (a move
the game drives). Walking on the ground again, or aiming, ends it. Speeds never decide when: Apex Movement lets the
player set a slide slower than the sprint (Kevin's 1130 against 1269), and a share of the sprint's speed cut his
slides short (first test). Speed only shapes how much: the gain follows the player down as he slows, so the view is
back when he stands still, not after (Kevin, third test: the view changing once he had stopped was disturbing).
"""

import math

from .easing import MAX_STEP_S, SETTLE_CONSTANTS, Easing
from .player_sample import Sample

# The game takes a frame or two between the sprint and its slide, or a landing and its slide: the second test ended
# runs at exactly the sprint's speed (1269) on that frame. Walking must last this long to end a run.
GROUND_GRACE_NS = 250_000_000
# The whole gain down to this share of the run's sprint speed (a slide at 1130 of 1269 keeps it all), then in step
# with the speed, to nothing at a standstill.
FULL_SHARE = 0.75
# The stages trail a steady slowdown by three time constants; the speed is read four ahead along its slope, so the
# view is nearly back when the player stands still (third test) and settles softly just after. Only braking on the
# ground is led: a landing's lost fall speed is not braking.
LEAD_CONSTANTS = 4.0
# How smoothly the braking is measured: one frame's jitter never jolts the view.
SLOPE_S = 0.05
# Close enough to call the view settled, so a run's end gives the FOV back instead of chasing a vanishing tail.
REST = 1e-3


class SpeedFov:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.gain = self.ceiling = self.top_speed = 0.0
        self.follow = 1.0
        self._slope = 0.0
        self._last_speed: float | None = None
        self.running = self.moved = False
        self._easing = Easing(1, REST)
        self._last_ns: int | None = None
        self._ground_ns: int | None = None

    def update(self, values: tuple[bool, float, float], sample: Sample | None, now_ns: int) -> float:
        enabled, gain, seconds = values
        step = 0.0 if self._last_ns is None else min(max((now_ns - self._last_ns) / 1e9, 0.0), MAX_STEP_S)
        self._last_ns = now_ns
        was_running = self.running
        self.running = enabled and self._running(sample, now_ns)
        if self.running and not was_running:
            self.top_speed, self._slope = 0.0, 0.0
        self._braking(sample, step)
        lead = LEAD_CONSTANTS * seconds / SETTLE_CONSTANTS
        self.follow = self._share(sample)
        ahead = self._share(sample, max(0.0, sample.speed + self._slope * lead)) if sample is not None else self.follow
        # The gain's setting, even switched off: the saved top stays put while the view comes back.
        self.ceiling = gain
        target = gain * ahead if self.running else 0.0
        previous, self.gain = self.gain, self._easing.step((target,), seconds, step)[0]
        self.moved = self.gain != previous
        return self.gain

    def _braking(self, sample: Sample | None, step: float) -> None:
        """The ground speed's fall per second, smoothed; nothing in the air, on landing or when speeding up."""
        on_ground = sample is not None and not sample.in_air
        if on_ground and self._last_speed is not None and step > 0:
            fall = min(0.0, (sample.speed - self._last_speed) / step)
            self._slope += (fall - self._slope) * (1.0 - math.exp(-step / SLOPE_S))
        else:
            self._slope = 0.0
        self._last_speed = sample.speed if on_ground else None

    def _share(self, sample: Sample | None, speed: float | None = None) -> float:
        """The run's share of the gain: all of it down to FULL_SHARE of the run's sprint speed, then the speed's."""
        if sample is None:
            return self.follow
        if self.running and (sample.sprinting or sample.sliding) and not sample.in_air:
            self.top_speed = max(self.top_speed, sample.speed)
        full = FULL_SHARE * self.top_speed
        if full <= 0 or sample.speed >= full:
            # Above the following zone the whole gain stays, however the speed changes: a dash's end is no braking.
            return 1.0
        return min(1.0, (sample.speed if speed is None else speed) / full)

    def _running(self, sample: Sample | None, now_ns: int) -> bool:
        if sample is None or sample.aiming:
            return False
        if sample.sprinting or sample.sliding or (self.running and (sample.in_air or sample.driven)):
            self._ground_ns = None
            return True
        if not self.running:
            return False
        if self._ground_ns is None:
            self._ground_ns = now_ns
        return now_ns - self._ground_ns < GROUND_GRACE_NS


def why(sample: Sample | None) -> str:
    """The log's reason for a change, so a test in game says which state started or ended a run."""
    if sample is None:
        return "no player"
    state = ("aiming" if sample.aiming else "sprint" if sample.sprinting else "slide" if sample.sliding
             else "air" if sample.in_air else "game move" if sample.driven else "ground")
    return f"{state} at {sample.speed:.0f}"


def step(speed: SpeedFov, settings, pc, now_ns: int) -> float:
    """One frame for the elected mod's settings; an adapter without the option never widens the view."""
    from .player_sample import read
    values = getattr(settings, "speed_fov", lambda: (False, 0.0, 1.0))()
    was_running = speed.running
    sample = read(pc) if values[0] or speed.gain > 0 else None
    gain = speed.update(values, sample, now_ns)
    if speed.running != was_running:
        settings.note(f"speed FOV {'widening' if speed.running else 'back'}: {why(sample)}")
    return gain
