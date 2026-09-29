"""Puts the heirloom away as the weapon comes back: both hands go down under the screen with it, then the weapon rises
from there into the game's own draw.

Why, 2026-09-25 (cosmetics/heirloom/docs/enquetes/2026-09-24-animations.md): Kevin wants "une animation fluide entre le
rangement des mains et la sortie de l'arme qui s'enchaîne", as in Apex, where he found the switch takes half a second
to a second longer than ours. The weapon cannot be held back: its draw starts inside the game, with no call a hook
sees before the weapon is in the hand (apex_weapon_calls.py, same day). So the weapon is hidden as it arrives, the
hands play our put-away (AS_UA_Unequip, which the game never plays, rebuilt from the rest to under the screen,
cosmetics/heirloom/jakobs_knife/heirloom.json, in our own folder), and as it ends the weapon shows again while the
arms blend from under the screen into the game's draw, already under way: the weapon rises from below. The game
itself equips the weapon as it always does.

The weapon is always shown again: when the hands are down, when the put-away is cut short, and when it fails. A
failure to play is said once and stops the put-aways until the knife is next put in a hand: the heirloom then goes at
once, as before.
"""

from typing import Any, Callable

from .apex_draw import SLOT
from .apex_moves_timing import Timing

Say = Callable[[str], None]
# The heirloom's own, in its folder (apex_anim_list.animation).
PUT_AWAY = "AS_UA_Unequip"
# The put-away starts on the rest's first image, the pose the hands hold: no blend is needed.
BLEND_IN_S = 0.0
# The blend out starts at the put-away's end, on the hands under the screen, and lasts the timing's rise.
BLEND_OUT_AT_END = 0.0


class PutAway:
    """The put-away, played on the arms with `timing` at each call until it fails once."""

    def __init__(self, load: Callable[[], Any], timing: Timing, pointer: Callable[[Any], Callable[[], Any]],
                 say: Say) -> None:
        """`pointer` keeps a game object without holding it alive: the SDK's WeakPointer."""
        self._load = load
        self._timing = timing
        self._pointer = pointer
        self._say = say
        self._broken = False
        self._weapon: Callable[[], Any] | None = None
        self._playing: Callable[[], Any] | None = None

    def start(self, arms_animation: Any, weapon: Any) -> float | None:
        """Hides `weapon` and plays the put-away; returns in how many seconds the hands are down, or None when it
        cannot play."""
        if self._broken:
            return None
        try:
            sequence = self._load()
            if sequence is None:
                self._stop("the put-away animation was not found")
                return None
            weapon.SetActorHiddenInGame(True)
            self._weapon = self._pointer(weapon)
            montage = arms_animation.PlaySlotAnimationAsDynamicMontage(
                Asset=sequence, SlotNodeName=SLOT, BlendInTime=BLEND_IN_S, BlendOutTime=self._timing.rise,
                InPlayRate=self._timing.away, LoopCount=1, BlendOutTriggerTime=BLEND_OUT_AT_END,
                InTimeToStartMontageAt=0.0)
            lasting = float(sequence.GetPlayLength()) / self._timing.away
        except Exception as error:
            self.finish()
            self._stop(f"the put-away could not be played ({type(error).__name__}: {error})")
            return None
        # The SDK may give output parameters after the return value.
        if isinstance(montage, tuple):
            montage = montage[0] if montage else None
        self._playing = self._pointer(montage) if montage is not None else None
        self._say(f"heirloom put away at {self._timing.away:g} times its speed, the weapon rising after "
                  f"{lasting:.2f} s over {self._timing.rise:g} s")
        return lasting

    def finish(self) -> None:
        """The hands are down: the weapon shows again, and rises as the arms blend back to the game's."""
        pointer, self._weapon = self._weapon, None
        weapon = pointer() if pointer is not None else None
        self._playing = None
        if weapon is None:
            return
        try:
            weapon.SetActorHiddenInGame(False)
        except Exception as error:
            self._say(f"the weapon could not be shown again ({type(error).__name__}: {error})")

    def cancel(self, arms_animation: Any) -> None:
        """Cut short (another weapon change, a climb): the put-away stops at once and the weapon shows."""
        pointer = self._playing
        self.finish()
        montage = pointer() if pointer is not None else None
        if montage is None:
            return
        try:
            if arms_animation.Montage_IsPlaying(montage):
                arms_animation.Montage_Stop(0.0, montage)
        except Exception as error:
            self._say(f"the put-away could not be stopped ({type(error).__name__}: {error})")

    def _stop(self, why: str) -> None:
        self._broken = True
        self._say(f"{why}: the heirloom goes at once, without its put-away, until the knife is next put in a hand")
