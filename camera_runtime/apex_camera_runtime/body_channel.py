"""The game's own body rotation aimed where the mod turns the body (body_facing.py), so the two never fight.

The game turns the walking hunter toward the camera every frame through its body rotation channel (tag
RotationChannel.Body): about 4 degrees a frame at 400 degrees a second, which the mod put back each frame. The
animation was told the hunter spun at 400 degrees a second, and the forward-left walk crossed his legs and twisted
his ankle (player report, 2026-10-12, docs/investigations/third_person_fov/animation/2026-10-12-jambes-emmelees.md).
Aimed at the mod's body (SetRotationTargetRotation), the channel turns him there itself: Kevin, trial 5, « tout était
parfait ». It is given back (SetRotationTargetDefault) the moment the mod lets go. Never paused: a paused channel
imposes its frozen rotation every frame (trial 4).
"""

from typing import Any, Callable

CHANNEL = "RotationChannel.Body"
LIBRARY = "GbxRotationBlueprintLibrary"
# The channel pulls the body toward its target by what separates them: under this, about 10 degrees a second at
# 100 frames a second, too little to show (trial 5 left up to half a degree, and Kevin saw nothing).
MIN_CHANGE = 0.1


def signed_gap(direction: float, reference: float) -> float:
    gap = (direction - reference + 180.0) % 360.0 - 180.0
    return 180.0 if gap == -180.0 else gap


class BodyChannel:
    """Owns the game's body channel while it is aimed: aim() each frame the mod holds the body, give_back() when it
    lets go. A refused call is said once and the channel left to the game for the session: the body still faces the
    run, as before this fix."""

    def __init__(self, find_class: Callable[[str], Any], make_tag: Callable[[str], Any],
                 make_rotator: Callable[[float, float, float], Any], weak: Callable[[Any], Any],
                 log: Callable[[str], None]) -> None:
        self.find_class, self.make_tag, self.make_rotator = find_class, make_tag, make_rotator
        self.weak, self.log = weak, log
        self.library: Any = None
        self.aimed_yaw: float | None = None
        self.held: Any = None  # the hunter whose channel is aimed, weakly
        self.held_id = 0
        self.broken = False

    def aim(self, character: Any, yaw: float) -> None:
        if self.broken:
            return
        try:
            address = int(character._get_address())
            if self.aimed_yaw is not None and address != self.held_id:
                self.give_back()  # another hunter now: the last one gets his channel back first
            if self.aimed_yaw is not None and abs(signed_gap(yaw, self.aimed_yaw)) < MIN_CHANGE:
                return
            if self.library is None:
                # A class default object lasts as long as the game.
                self.library = self.find_class(LIBRARY).ClassDefaultObject
            # Marked before the call, so whatever comes next gives the channel back, even after a refused call.
            self.aimed_yaw, self.held, self.held_id = yaw, self.weak(character), address
            self.library.SetRotationTargetRotation(Actor=character, ChannelTag=self.make_tag(CHANNEL),
                                                   InRotation=self.make_rotator(0.0, yaw, 0.0))
        except Exception as error:
            self._break(error)

    def give_back(self) -> None:
        if self.aimed_yaw is None:
            return
        held, self.aimed_yaw, self.held, self.held_id = self.held, None, None, 0
        character = held() if held is not None else None
        if character is None:
            return  # gone with the hunter: nothing left to give back
        try:
            self.library.SetRotationTargetDefault(Actor=character, ChannelTag=self.make_tag(CHANNEL))
        except Exception as error:
            self._break(error)

    def _break(self, error: Exception) -> None:
        first = not self.broken
        self.broken = True
        if self.aimed_yaw is not None:
            self.give_back()
        if first:
            self.log(f"body rotation channel left to the game for the session: {type(error).__name__}")
