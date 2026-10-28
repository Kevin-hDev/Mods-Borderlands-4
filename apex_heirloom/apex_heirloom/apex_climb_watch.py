"""Tells whether the hands are climbing: on a ladder or one of the game's climbing walls, over a ledge, or in Apex
Movement's wall climb.

Why, 2026-09-24 (cosmetics/heirloom/docs/heirloom.md, section 15): those moves keep the game's arm animations, where
the hand holds nothing, and Kevin wants them without the knife. What each reads is verified in game
(borderlands_4/mouvements_borderlands_4.md, section 5 bis):
- a ladder or a game climbing wall: movement.LadderState.CurrentClimbable points to it while the player is on it;
- a ledge: movement.ReplicatedMantleState.ActionIndex goes from -1 to 0 for the whole mantle;
- Apex Movement's wall climb plays AS_Wall_Climb_U on the arms, as a montage the game makes for it in the FullBody
  slot (its climb_animation.py). That montage is transient (/Engine/Transient.AnimMontage_N, seen 2026-09-23): the
  animation is read from its slot track. Apex Grapple plays in the same slot, and does not count.
"""

from typing import Any, Callable

Say = Callable[[str], None]
LADDER, LEDGE, WALL = "ladder", "ledge", "wall climb"
WALL_CLIMB_PREFIX = "AS_Wall_Climb"
# One line per kind of unreadable field, not one per frame: the watch runs at every frame.
REPORTED: set[str] = set()


def _unreadable(kind: str, error: Exception, say: Say) -> None:
    if kind not in REPORTED:
        REPORTED.add(kind)
        say(f"the {kind} could not be read ({type(error).__name__}): the heirloom stays shown during it")


def montage_animation(montage: Any) -> str:
    """The name of the animation a montage plays first, from its first slot track; "" when it has none."""
    for track in montage.SlotAnimTracks:
        for segment in track.AnimTrack.AnimSegments:
            played = segment.AnimReference
            if played is not None:
                return str(played.Name)
    return ""


def climbing(movement: Any, arms_animation: Any, say: Say) -> str:
    """LADDER, LEDGE or WALL while that move goes on, "" otherwise. A field that cannot be read counts as not
    climbing: the knife then shows through the move, which Kevin would see, and the reason is in the log."""
    try:
        if movement.LadderState.CurrentClimbable is not None:
            return LADDER
    except (AttributeError, TypeError, ValueError) as error:
        _unreadable(LADDER, error, say)
    try:
        if int(movement.ReplicatedMantleState.ActionIndex) >= 0:
            return LEDGE
    except (AttributeError, TypeError, ValueError) as error:
        _unreadable(LEDGE, error, say)
    try:
        montage = arms_animation.GetCurrentActiveMontage()
        if montage is not None and montage_animation(montage).startswith(WALL_CLIMB_PREFIX):
            return WALL
    except (AttributeError, TypeError, ValueError) as error:
        _unreadable(WALL, error, say)
    return ""
