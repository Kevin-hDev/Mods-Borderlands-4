"""A player's grapple look as one number, so that the other players draw that player's grapple as that player chose it
(Kevin, 17 October 2026: "chaque joueur conserve son grappin").

Whether the rope shows at all, then the look's settings in their own order (look_settings.ALL), each the place of its
value among its choices: every look fits in under 2^21 numbers, small enough for the 30 bits a guest's message to the
host carries (coop_code.py). A player who hides the rope hides it for everyone.
A number this build cannot read gives the rope shown in the first value of each setting, never an error: a guest
may run another build.
"""

from dataclasses import dataclass

from . import look_settings, settings

SETTINGS = look_settings.ALL
COUNT = 2
for _option in SETTINGS:
    COUNT *= len(_option.choices)


@dataclass(frozen=True)
class Look:
    """One player's look: whether the rope shows, and the settings by their identifiers: look, rope_look, ..."""
    shown: bool
    values: tuple[str, ...]

    def __getattr__(self, name: str) -> str:
        for option, value in zip(SETTINGS, self.values):
            if option.identifier == name:
                return value
        raise AttributeError(name)


def encode(shown: bool, values: tuple[str, ...]) -> int:
    number = 1 if shown else 0
    for option, value in zip(SETTINGS, values):
        number = number * len(option.choices) + list(option.choices).index(value)
    return number


def decode(number: int) -> Look:
    if not 0 <= number < COUNT:
        # Shown: a rope seen in the first look beats a rope missing for a number of another build.
        number = COUNT // 2
    values = []
    for option in reversed(SETTINGS):
        number, place = divmod(number, len(option.choices))
        values.append(option.choices[place])
    return Look(number == 1, tuple(reversed(values)))


def mine() -> int:
    """The player's own look, as set now."""
    return encode(bool(settings.show_rope.value), tuple(option.value for option in SETTINGS))
