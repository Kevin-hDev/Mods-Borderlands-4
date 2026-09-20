"""A faster glide: the game's own glide, with a higher top speed, in every direction.

Kevin, 2026-09-20: the glide "est trop lente actuellement". It already goes sideways and backwards — measured the
same day, the angle between the glide and the camera reaches 179 degrees and the speed tops out at 1200 whatever the
direction. So there is nothing to open, only a ceiling to lift.

The lever is the movement component's `GlidingSpeed` attribute, and only that one: written at 1560, the glide reached
1424 where the game caps at 1200, while `GlidingSpeedBoost` and `LiveGlideSettings.GlidingSpeed` changed nothing on
four glides (2026-09-20, verified in game). The name trap of the dash, twice over.

What is written is a ceiling the glide climbs to at `GlidingAcceleration` a second, from about 828. At the game's 400
a second, 1200 arrives after 0.9 s and 1560 after 1.8 s: raised alone, the ceiling would do nothing to a short glide
and the setting would read as broken. So the acceleration is raised by the same percentage.

The descent is left alone, as Kevin asked: gravity scale and terminal velocity stay the game's. A glide that goes
faster at the same fall rate covers more ground; the two cannot be separated.
"""

from typing import Any

from . import ownership, report, settings

# One entry per attribute this movement owns: the key ownership knows it by, and its field on the movement component.
FIELDS: tuple[tuple[str, str], ...] = (
    ("movement.GlidingSpeed", "GlidingSpeed"),
    ("movement.GlidingAcceleration", "GlidingAcceleration"),
)


def reset() -> None:
    """Nothing of its own to forget: the game's values belong to ownership, which stop gives back."""


def _pair(movement: Any, name: str) -> Any:
    return getattr(movement, name, None)


def _read(pair: Any) -> tuple[float, float]:
    return float(pair.BaseValue), float(pair.Value)


def _put(movement: Any, name: str, values: tuple[float, float]) -> None:
    # The struct is assigned back into the movement component: the SDK may hand out a copy, and a field written on
    # that copy changes nothing in the game. That is the lesson the slide speed cost five mod versions to learn.
    pair = _pair(movement, name)
    pair.BaseValue, pair.Value = values
    setattr(movement, name, pair)


def _hold(movement: Any, key: str, name: str, factor: float) -> None:
    pair = _pair(movement, name)
    if pair is None:
        # A game update that renames the field: the glide stays the game's own rather than the movement failing.
        report.error_once(key, f"the game has no {name} any more: the glide keeps the game's own speed")
        return
    def read() -> tuple[float, float]:
        return _read(_pair(movement, name))

    def put(values: tuple[float, float]) -> None:
        _put(movement, name, values)

    game = ownership.original(key) if ownership.is_owned(key) else read()
    wanted = (game[0] * factor, game[1] * factor)
    if all(abs(now - target) <= ownership.SPEED_TOLERANCE for now, target in zip(read(), wanted)):
        ownership.claim(key, ownership.CHARACTER, read, put)
        return
    ownership.write(key, ownership.CHARACTER, read, put, wanted)
    report.note(f"glide {name} {wanted[0]:.0f} (game {game[0]:.0f})")


def update(character: Any, now_ns: int) -> None:
    movement = character.CharacterMovement
    factor = float(settings.glide_speed.value) / 100.0
    for key, name in FIELDS:
        _hold(movement, key, name, factor)


def stop(character: Any) -> None:
    for key, _name in FIELDS:
        ownership.restore(key)
