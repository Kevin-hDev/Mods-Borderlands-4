"""With OMNI DIRECTION, every slide starts the way the hunter runs, in the three camera mods (Kevin, 2026-10-09: "c'est
le but d'un mouvement omnidirectionnel").

The game's slide starts toward the aim (ParentAimDirection2D), whatever the run: verified in game on 2026-09-19 with
Omni Sprint alone. Apex Movement's momentum slides (slide_direction.py) set ParentVelocity2D, verified on 2026-09-16:
nine landing slides left within a degree of the jump's direction. This unit writes the same value while omni direction
is on. Apex Movement writes it on its own too, as its separate Slides file carries no camera runtime: each writes only
what it finds missing and gives back only what it wrote, so the two meet on the same value, and when one gives back
the other's next check writes it again.
"""

from typing import Any, Callable

SLIDE_ASSET = ("OakControlledMove", "/Game/PlayerCharacters/_Shared/Tricks/ControlledMoves/Move_Slide.Move_Slide")
MOMENTUM = "ParentVelocity2D"
# Twice a second: Move_Slide is unloaded at the title screen and comes back with the game's value at the next load.
CHECK_NS = 500_000_000


class SlideLaunch:
    def __init__(self, find: Callable[..., Any], log: Callable[[str], None]) -> None:
        self.find, self.log = find, log
        self.original: Any = None
        self.next_ns = 0

    def _asset(self) -> Any:
        try:
            return self.find(*SLIDE_ASSET)
        except ValueError:
            # Not loaded (title screen, level load): looked up again at the next check.
            return None

    @staticmethod
    def _put(asset: Any, value: Any) -> None:
        launch = asset.LaunchDirection
        launch.RelativeDirection = value
        # Assigned back whole: the SDK may hand out a copy of the struct, and a field written on a copy changes nothing.
        asset.LaunchDirection = launch

    def update(self, wanted: bool, now_ns: int) -> None:
        if now_ns < self.next_ns:
            return
        self.next_ns = now_ns + CHECK_NS
        if not wanted:
            self.give_back()
            return
        asset = self._asset()
        if asset is None:
            return
        current = asset.LaunchDirection.RelativeDirection
        if current.name == MOMENTUM:
            return
        self.original = current
        self._put(asset, type(current)[MOMENTUM])
        self.log(f"slides follow the run (was {current.name})")

    def give_back(self) -> None:
        """The game's direction back, only over the value this unit wrote."""
        if self.original is None:
            return
        original, self.original = self.original, None
        self.next_ns = 0
        asset = self._asset()
        # Unloaded since: the game loads it again with its own value, nothing to give back.
        if asset is not None and asset.LaunchDirection.RelativeDirection.name == MOMENTUM:
            self._put(asset, original)
            self.log(f"slides start toward the aim again ({original.name})")
