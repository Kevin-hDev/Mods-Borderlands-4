"""The OMNI DIRECTION settings, shared by the three camera mods (Kevin, 2026-10-09; defaults and reasons in
docs/investigations/apex_movement/animation/2026-10-09-corps-gauche-droite.md).

The two-box choices (360 or 180 degrees, dash or slide) are hidden sliders with two values, as the sniper optics are:
the window draws the boxes, and a number would mean nothing in the SDK's text menu.
"""

from dataclasses import dataclass

from mods_base import BoolOption, SliderOption

from . import option_texts

FULL_TURN, HALF_TURN = 0, 1
DASH, SLIDE = 0, 1


@dataclass(frozen=True)
class OmniValues:
    body: bool
    full_turn: bool
    # Sprint in every direction in third person; Omni Sprint opens it with its own switch instead.
    sprint: bool
    dash: bool


def choice(value: object, default: int) -> int:
    """0 or 1; a hand-edited value reads as the default."""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return value if type(value) is int and value in (0, 1) else default


class OmniDirectionOptions:
    def __init__(self, crouch_default: int, third_person_sprint: bool = True) -> None:
        """crouch_default: SLIDE in Apex Movement, a move of its own (Kevin), DASH elsewhere. Omni Sprint has no
        third-person sprint switch here: its OMNI SPRINT page opens the sprint in every view."""
        self.crouch_default = crouch_default
        self.body = BoolOption("omni_body", True, **option_texts.OMNI_BODY)
        self.angle = SliderOption("omni_angle", FULL_TURN, 0, 1, step=1, is_integer=True, is_hidden=True,
                                  **option_texts.OMNI_ANGLE)
        self.sprint = (BoolOption("omni_direction_sprint", True, **option_texts.OMNI_SPRINT)
                       if third_person_sprint else None)
        self.crouch = SliderOption("omni_crouch", crouch_default, 0, 1, step=1, is_integer=True, is_hidden=True,
                                   **option_texts.OMNI_CROUCH)
        self.options = [option for option in (self.body, self.angle, self.sprint, self.crouch) if option is not None]

    def values(self) -> OmniValues:
        body = self.body.value is True
        sprint = self.sprint is not None and self.sprint.value is True
        return OmniValues(body, choice(self.angle.value, FULL_TURN) == FULL_TURN, body and sprint,
                          choice(self.crouch.value, self.crouch_default) == DASH)
