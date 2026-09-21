"""The arms' grapple animation: the game's own, played on the first-person arms as a montage.

The lesson comes from Apex Movement's wall climb, and Kevin named it himself on 2026-09-20: writing
the values that drive the arms' graph showed nothing at all across five sessions, while playing the
game's animation as a dynamic montage moved the hands exactly as the game does.

The animation is `AS_Grapple`, named by the game's own grapple settings (`timingreferenceanim` in
Nexus-Data-Grapple4.ncs, decoded on 2026-09-18). Whether it can be played this way is *not verified*.

A failure switches the animation off alone, once, and the grapple itself goes on: a pull that works
without hands is worth more than no pull at all.
"""

from typing import Any

from unrealsdk import unreal

from . import arms, game, report

# The slot the game's own climb used, which covers the whole arms rig and lets go of the weapon.
SLOT = "FullBody"
BLEND_S = 0.2
# Blending into the held pose is quicker: the throw has just finished and the hand should not drift.
HOLD_BLEND_S = 0.05
# A play rate this small is a still image. The montage then lasts the animation's length divided by
# it — hours — so the hand stays where it is until the rope lets go and the slot is stopped.
FROZEN_RATE = 0.001
# Where in the animation the hand holds the rope, as a share of its length. The throw runs before
# it; past it the game's animation lets go, which is what looped during a pull (Kevin, 2026-09-20:
# "a partir du moment ou le grapin est accroche l'animation de main se repete en boucle").
HOLD_AT = 0.8

_playing = False
_holding = False
_broken = False
_announced = False
_owner: Any = None
_montage: Any = None
_release_pending = False


def reset() -> None:
    global _playing, _holding, _broken, _announced
    stop()
    _broken = _announced = False
    arms.forget()


def start() -> None:
    global _playing, _announced
    if _broken or _playing:
        return
    try:
        hands = arms.find(game.character())
        sequence = game.grapple_animation()
        if hands is None or sequence is None:
            report.error_once("animation:missing",
                              "the grapple animation is unavailable: the arms or AS_Grapple were not found")
            return
        # Once, not looping: the throw happens while the hook flies, and hold() takes over after it.
        montage = hands.PlaySlotAnimationAsDynamicMontage(Asset=sequence, SlotNodeName=SLOT, BlendInTime=BLEND_S,
                                                BlendOutTime=BLEND_S, InPlayRate=1.0, LoopCount=1,
                                                BlendOutTriggerTime=-1.0, InTimeToStartMontageAt=0.0)
        _remember(hands, montage)
        if not _announced:
            _announced = True
            report.note(f"grapple animation playing on the arms, {float(sequence.GetPlayLength()):.2f}s long")
    except Exception as exc:
        _fail(exc)


def hold() -> None:
    """Freezes the hand on the pose that holds the rope, until the rope lets go.

    The same animation replayed from its holding moment at a rate near zero: a still image rather
    than a loop. There is no way to pause a montage from here, and letting it run played the whole
    throw again and again for the length of a pull.
    """
    global _holding
    if _broken or _holding or _release_pending:
        return
    try:
        hands = arms.find(game.character())
        sequence = game.grapple_animation()
        if hands is None or sequence is None:
            return
        at = float(sequence.GetPlayLength()) * HOLD_AT
        montage = hands.PlaySlotAnimationAsDynamicMontage(Asset=sequence, SlotNodeName=SLOT, BlendInTime=HOLD_BLEND_S,
                                                BlendOutTime=BLEND_S, InPlayRate=FROZEN_RATE, LoopCount=1,
                                                BlendOutTriggerTime=-1.0, InTimeToStartMontageAt=at)
        _remember(hands, montage)
        _holding = True
        report.note(f"grapple hand held at {at:.2f}s of the animation")
    except Exception as exc:
        _fail(exc)


def stop() -> None:
    global _playing, _holding, _owner, _montage, _release_pending
    if _montage is None:
        return
    try:
        hands, montage = _owner(), _montage()
        if hands is not None and montage is not None:
            # Never stop FullBody: a climb or mantle may already own that slot.
            hands.Montage_Stop(BLEND_S, montage)
    except Exception:
        # Keep one owned resource for a later retry; do not stack another montage over it.
        _release_pending = True
        report.error_once("animation:stop", "the grapple hand could not be released; cleanup will be retried")
        return
    _owner = _montage = None
    _playing = _holding = _release_pending = False


def _remember(hands: Any, montage: Any) -> None:
    global _owner, _montage, _playing
    # The SDK may include output parameters after the return value.
    if isinstance(montage, tuple):
        montage = montage[0] if montage else None
    if montage is None:
        raise RuntimeError("the game did not return the grapple montage")
    _owner, _montage = unreal.WeakPointer(hands), unreal.WeakPointer(montage)
    _playing = True


def _fail(exc: Exception) -> None:
    global _broken
    _broken = True
    report.error_once("animation", f"the grapple animation was switched off after an error: {exc!r}")
    stop()
