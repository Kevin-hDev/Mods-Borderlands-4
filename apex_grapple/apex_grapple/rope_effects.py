"""Fan out existing rope lifecycle events without altering movement or visuals."""

from typing import Any

from . import rope_audio, rope_visuals


def reset() -> None:
    rope_audio.reset()
    rope_visuals.reset()


def start(character: Any, anchor: tuple, now_ns: int, flight_s: float) -> None:
    rope_audio.start(character)
    rope_visuals.start(character, anchor, now_ns, flight_s)


def follow(character: Any, anchor: tuple) -> None:
    # The next update after contact begins traction. No timer or delay is added
    # to movement, and hiding the rope must not disable its sounds.
    rope_audio.pull(character)
    rope_visuals.follow(character, anchor)


def hold(character: Any, now_ns: int, start_gap: float, near: float, pull_cap: float) -> None:
    """The hook bites `start_gap` cm away; the pull lets go `near` cm from the anchor and adds up to `pull_cap`."""
    rope_audio.attach()
    rope_visuals.hold(character, now_ns, start_gap, near, pull_cap)


def pulled(to_anchor: tuple, velocity: tuple) -> None:
    """One frame of the pull, as numbers: the way left to the anchor and the velocity written."""
    rope_visuals.pulled(to_anchor, velocity)


def stop(now_ns: int) -> None:
    rope_audio.stop()
    rope_visuals.stop(now_ns)


def tick(character: Any, now_ns: int) -> None:
    """Every frame, a shot running or not: the grapple gun's hook keeps coming back after the pull has ended."""
    rope_visuals.tick(character, now_ns)
