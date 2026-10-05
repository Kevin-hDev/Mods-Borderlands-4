"""Single immutable framing catalog; native limits are generated from this source."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Group:
    key: str
    title: str
    default: int
    minimum: int
    maximum: int
    presets: tuple[tuple[str, int], ...]
    step: int = 1

    def valid(self, value) -> bool:
        return (type(value) is int and self.minimum <= value <= self.maximum
                and (value - self.minimum) % self.step == 0)


# Percentages describe actual projected effects, never fractions of an internal offset.
GROUPS = (
    Group("zoom", "Aim Zoom", 15, 0, 50, (("Wide", 0), ("Standard", 15), ("Close", 25))),
    Group("horizontal", "Shoulder Spacing", 10, 0, 50,
          (("Tight", 0), ("Standard", 10), ("Open", 20))),
    Group("height", "Camera Height", 0, -50, 50,
          (("Standard", 0), ("Higher", 10), ("Lower", -10))),
)

OPTION_PREFIX = "camera_framing_"
CUSTOM_SUFFIX = "_custom"
INVALID_SETTING_NOTE = "Camera framing setting invalid; using its default"


def group(key: str) -> Group:
    if type(key) is str:
        for item in GROUPS:
            if key == item.key:
                return item
    raise ValueError("invalid framing group")
