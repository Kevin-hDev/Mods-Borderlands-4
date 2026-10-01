"""Plays the chosen heirloom's inspection on the arms at a press of its key (inspect_keys.py): a short flourish of the
heirloom in the right hand, as Wraith turns her kunai in Apex Legends, over whatever the arms play.

Why, 2026-09-29 (cosmetics/heirloom/docs/heirloom.md, section 20): Kevin wants it played "partout", standing, walking,
running, crouched or sliding, the left hand keeping its own motion, and only drawing the weapon stops it before its
end. It is an additive animation, a change laid over the arms' own, played as a dynamic montage the way the draw is.
Why the draw's FullBody slot, 2026-10-01 (cosmetics/heirloom/docs/enquetes/2026-09-29-inspection.md): in the ADD slot
the arm followed it but the game put the heirloom's bone (R_Hand_Object) back in its grip right after (the arms'
graph, LayeredBoneBlend_9), so the axe never turned; in FullBody, after that, the axe turns as built, the left hand
untouched, at rest, walking and running (verified in game on 2026-09-30 and 2026-10-01).
Why its own animation while crouched, 2026-10-01: the game adds it to the pose the arms are in. Over the crouched arms,
which hold the heirloom low in the middle, the one built on the rest went up and its axe's head left the screen at the
top as it turned (verified in game); the one built on the crouched rest plays the keys as Kevin validated them. The
stance is read at each press.
Why no fade from the rest, 2026-09-30 (sondes/apex_inspect_trial.py): the inspection starts from the rest and comes
back to it; a fade would play the axe's 0.2 s raise at part weight, short of its first key.
Why a press during it starts from its first key, Kevin, 2026-09-30: "il faut pouvoir enchaîner le mouvement". In Apex a
repetition started during the previous one does not go back to the rest: the fist catching the axe goes straight into
the raised axe. The new montage starts at the first key's time (heirloom_catalog.py, "again_at") and fades in briefly,
so the hand goes from where it is to the raised heirloom; the engine fades the one it replaces in the slot's group out
as long (its Montage_Play, not verified in game). One gesture per press, a new press restarting it without waiting for
its end (Kevin, 2026-09-25, heirloom.md, section 17).

A heirloom without an inspection does nothing on the key (the knife, until it has its own), said once. An inspection
that cannot be found or played is said once and stops the inspections until the heirloom is next put in a hand.
"""

from typing import Any, Callable

from .apex_draw import SLOT
from .heirloom_catalog import HEIRLOOMS

Say = Callable[[str], None]
BLEND_IN_S = 0.0
# Kevin's "enchaîner", 2026-09-30: from wherever the hand is to the raised heirloom.
AGAIN_BLEND_IN_S = 0.1
# It ends at the rest, where the arms already are.
BLEND_OUT_S = 0.0
# A line per press, bounded per heirloom put in a hand: presses must not fill the log, which the game only rewrites at
# its next launch.
MAX_TOLD = 200


def inspection(heirloom: str) -> dict | None:
    """The heirloom's inspection as the catalog gives it, its animation's name, the crouched one's, and the time a
    press during it starts from; None when it has none."""
    return HEIRLOOMS[heirloom]["inspect"]


class Inspect:
    """The chosen heirloom's inspection, played on the arms at each press until it fails once."""

    def __init__(self, heirloom: Callable[[], str], crouched: Callable[[], bool], load: Callable[[str], Any],
                 pointer: Callable[[Any], Callable[[], Any]], say: Say) -> None:
        """`heirloom` gives the heirloom chosen now, `crouched` whether the player is crouched now, `load` one of its
        animations by name or None; `pointer` keeps a game object without holding it alive: the SDK's WeakPointer."""
        self._heirloom = heirloom
        self._crouched = crouched
        self._load = load
        self._pointer = pointer
        self._say = say
        self._broken = False
        self._none_said = False
        self._told = 0
        self._playing: Callable[[], Any] | None = None

    def play(self, arms_animation: Any) -> None:
        """From its start with no fade, or from its first key with a short fade while it still plays."""
        if self._broken:
            return
        try:
            name = self._heirloom()
            known = inspection(name)
            if known is None:
                self._no_inspection(name)
                return
            crouched = bool(self._crouched())
            animation = known["crouched"] if crouched else known["animation"]
            again = self._still_playing(arms_animation)
            start, blend = (known["again_at"], AGAIN_BLEND_IN_S) if again else (0.0, BLEND_IN_S)
            sequence = self._load(animation)
            if sequence is None:
                self._stop(f"the {name}'s inspection {animation} was not found")
                return
            montage = arms_animation.PlaySlotAnimationAsDynamicMontage(
                Asset=sequence, SlotNodeName=SLOT, BlendInTime=blend, BlendOutTime=BLEND_OUT_S, InPlayRate=1.0,
                LoopCount=1, BlendOutTriggerTime=-1.0, InTimeToStartMontageAt=start)
        except Exception as error:
            self._stop(f"the inspection could not be played ({type(error).__name__}: {error})")
            return
        # The SDK may give output parameters after the return value.
        if isinstance(montage, tuple):
            montage = montage[0] if montage else None
        self._playing = self._pointer(montage) if montage is not None else None
        self._tell(f"{name} inspected {'crouched ' if crouched else ''}{'again ' if again else ''}from {start:g} s")

    def cancel(self, arms_animation: Any) -> None:
        """Stops the inspection at once if it still plays, leaving any other montage alone."""
        pointer, self._playing = self._playing, None
        montage = pointer() if pointer is not None else None
        if montage is None:
            return
        try:
            if arms_animation.Montage_IsPlaying(montage):
                arms_animation.Montage_Stop(0.0, montage)
                self._say("inspection stopped: the heirloom left the empty hand while it played")
        except Exception as error:
            self._say(f"the inspection could not be stopped ({type(error).__name__}: {error})")

    def _still_playing(self, arms_animation: Any) -> bool:
        montage = self._playing() if self._playing is not None else None
        return montage is not None and bool(arms_animation.Montage_IsPlaying(montage))

    def _no_inspection(self, name: str) -> None:
        if not self._none_said:
            self._none_said = True
            self._say(f"the {name} has no inspection: its key does nothing")

    def _tell(self, text: str) -> None:
        if self._told < MAX_TOLD:
            self._told += 1
            self._say(text)

    def _stop(self, why: str) -> None:
        self._broken = True
        self._say(f"{why}: no inspection until the heirloom is next put in a hand")
