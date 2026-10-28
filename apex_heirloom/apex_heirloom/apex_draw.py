"""Plays the heirloom's draw on the arms as the weapon goes away: both hands rise from under the screen, the heirloom in
the right one. When the rise starts and how fast it plays are set in the menu (settings.py, apex_moves_timing.py).

Why, 2026-09-24 (cosmetics/heirloom/docs/heirloom.md, section 15): Kevin wants the weapon put away as Holster Your
Weapon does, "puis les deux main arrive du bas avec le heirloom dans la main droite". The game switches the arms from
the weapon's animations to the unarmed ones in one image and never plays AS_UA_Equip, the unarmed draw: our container
holds the heirloom's draw under that name in our own folder (cosmetics/heirloom/jakobs_knife/heirloom.json,
apex_anim_list.py), and this plays it the way Apex Grapple plays AS_Grapple, verified in game on 2026-09-20: a dynamic
montage in the FullBody slot, which covers the whole arms. Played once, it gives the arms back to the game as it ends.
Why the rise starts late, 2026-09-25: played from its start, "les mains mettent beaucoup de temps à apparaître"
(Kevin). The draw leaves 40 cm under the hold and starts slowly, so the hands stay under the screen for about its
first 0.35 s of 0.67 (worked out from the pose, the view's edge not measured). Started later, it rises from just
under the screen at speed and slows into the hold. Kevin set it in game the same day with the console command,
from 0.4 s at 0.8 times its speed: "c'est très bien".

Why a draw is stopped, 2026-09-25 (log of Kevin's first trial): switching weapons, the game says "no weapon" and then
the new weapon within 1 to 20 ms. The draw started at the first and played on over the weapon's arms for its whole
length. It now stops at once, and only it (a climb may own the same slot), as soon as the heirloom is hidden again.

A failure to play is said once and stops the draws until the knife is next put in a hand: the heirloom still shows,
at once as before.
"""

from typing import Any, Callable

from .apex_moves_timing import Timing

Say = Callable[[str], None]
# The heirloom's own, in its folder (apex_anim_list.animation).
DRAW = "AS_UA_Equip"
SLOT = "FullBody"
# The hands start under the screen: blending in would first show the rest's hands sinking there.
BLEND_IN_S = 0.0
# The draw ends on the rest's first image while the game's rest has played on as long: a short blend joins them.
BLEND_OUT_S = 0.15


class Draw:
    """The draw, played on the arms with `timing` at each call until it fails once."""

    def __init__(self, load: Callable[[], Any], timing: Timing, pointer: Callable[[Any], Callable[[], Any]],
                 say: Say) -> None:
        """`pointer` keeps a game object without holding it alive: the SDK's WeakPointer."""
        self._load = load
        self._timing = timing
        self._pointer = pointer
        self._say = say
        self._broken = False
        self._playing: Callable[[], Any] | None = None

    def play(self, arms_animation: Any) -> None:
        if self._broken:
            return
        try:
            sequence = self._load()
            if sequence is None:
                self._stop("the draw animation was not found")
                return
            montage = arms_animation.PlaySlotAnimationAsDynamicMontage(
                Asset=sequence, SlotNodeName=SLOT, BlendInTime=BLEND_IN_S, BlendOutTime=BLEND_OUT_S,
                InPlayRate=self._timing.speed, LoopCount=1, BlendOutTriggerTime=-1.0,
                InTimeToStartMontageAt=self._timing.start)
        except Exception as error:
            self._stop(f"the draw could not be played ({type(error).__name__}: {error})")
            return
        # The SDK may give output parameters after the return value.
        if isinstance(montage, tuple):
            montage = montage[0] if montage else None
        self._playing = self._pointer(montage) if montage is not None else None
        self._say(f"heirloom drawn from {self._timing.start:g} s at {self._timing.speed:g} times its speed")

    def cancel(self, arms_animation: Any) -> None:
        """Stops the draw at once if it still plays, leaving any other montage of the slot alone."""
        pointer, self._playing = self._playing, None
        montage = pointer() if pointer is not None else None
        if montage is None:
            return
        try:
            if arms_animation.Montage_IsPlaying(montage):
                arms_animation.Montage_Stop(0.0, montage)
                self._say("draw stopped: the heirloom was hidden while it played")
        except Exception as error:
            self._say(f"the draw could not be stopped ({type(error).__name__}: {error})")

    def _stop(self, why: str) -> None:
        self._broken = True
        self._say(f"{why}: the heirloom shows at once, without its draw, until the knife is next put in a hand")
