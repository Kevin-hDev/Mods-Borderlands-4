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


# Percentages describe actual projected effects, never fractions of an internal offset. Spacing and height are shares of
# the hunter's sideways distance from the crosshair, 61.5 cm (shoulder_offset.py). Kevin, 2026-10-11, wants the player
# to place the crosshair anywhere around the hunter: from against the shoulder (-60 %, 25 cm from the body's middle) to
# twice the standard gap (+120 %), from the ankles (-240 %) to above the head (+100 %), looking straight ahead (body
# 186 cm, pivot 71 cm above its middle).
GROUPS = (
    Group("zoom", "Aim Zoom", 15, 0, 50, (("Wide", 0), ("Standard", 15), ("Close", 25))),
    Group("horizontal", "Shoulder Spacing", 10, -60, 120,
          (("Tight", -40), ("Standard", 10), ("Open", 60))),
    Group("height", "Camera Height", 0, -240, 100,
          (("Lower", -40), ("Standard", 0), ("Higher", 40))),
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
