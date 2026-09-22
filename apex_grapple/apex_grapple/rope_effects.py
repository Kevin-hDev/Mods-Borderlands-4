"""Fan out existing rope lifecycle events without altering movement or visuals."""

from typing import Any

from . import rope_audio, rope_visuals


def reset() -> None:
    rope_audio.reset()
    rope_visuals.reset()


def start(character: Any, anchor: tuple) -> None:
    rope_audio.start(character)
    rope_visuals.start(character, anchor)


def follow(character: Any, anchor: tuple) -> None:
    # The next update after contact begins traction. No timer or delay is added
    # to movement, and hiding the rope must not disable its sounds.
    rope_audio.pull(character)
    rope_visuals.follow(character, anchor)


def hold() -> None:
    rope_audio.attach()
    rope_visuals.hold()


def stop() -> None:
    rope_audio.stop()
    rope_visuals.stop()
