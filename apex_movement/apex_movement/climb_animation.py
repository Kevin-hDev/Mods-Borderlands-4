"""The arms' climbing animation during a wall climb (phase 2): the game's own first-person climb up, as a montage.

Session G (2026-09-17): AS_Wall_Climb_U played on the arms as a montage moved the hands "exactly" as on the game's
climbing walls (Kevin), in FullBody, Upperbody, Arms and DefaultSlot alike, while writing the values that drive the
arms' graph never showed anything (sessions C to G). FullBody, because the game's own climb lets go of the weapon
entirely and that slot covers the whole arms rig. The montage the game returns is not kept: once ended the game may
free it, and a freed object handed back to the game can crash it. So a climb's end stops the slot by name, and the loop
count ends the montage by itself soon after the longest climb the rules let live (climb_rules.longest_climb_ns): held
back against the wall, a climb lasts well past what its speed alone would take. A failure is reported once and turns
the animation alone off until the next character or switch-on, so the climb itself goes on.
"""

import math

from . import arms, climb_body, game, report

SLOT = "FullBody"
# The blend session G used: the hands eased in and out.
BLEND_S = 0.2

_playing = False
_broken = False
# The log shows the animation played once per character, not once per climb.
_announced = False


def start(longest_climb_s: float, wall: object | None = None) -> None:
    global _playing, _announced
    climb_body.start(game.character(), wall, longest_climb_s)
    if _broken:
        return
    try:
        hands, sequence = arms.find(game.character()), game.climb_animation()
        if hands is None or sequence is None:
            report.error_once("climb_animation:missing", "climb animation unavailable: the arms or the animation "
                                                         "were not found")
            return
        # One loop more than the longest climb needs, so a missed stop ends the hands within one loop.
        loops = math.ceil(longest_climb_s / float(sequence.GetPlayLength())) + 1
        hands.PlaySlotAnimationAsDynamicMontage(Asset=sequence, SlotNodeName=SLOT, BlendInTime=BLEND_S,
                                                BlendOutTime=BLEND_S, InPlayRate=1.0, LoopCount=loops,
                                                BlendOutTriggerTime=-1.0, InTimeToStartMontageAt=0.0)
        _playing = True
        if not _announced:
            _announced = True
            report.note(f"climb animation playing on the arms, {loops} loops at most")
    except Exception as exc:
        _fail(exc)


def stop() -> None:
    global _playing
    climb_body.stop()
    if not _playing:
        return
    _playing = False
    try:
        hands = arms.find(game.character())
        if hands is not None:
            # Stops only the montages this animation played on the slot, not the game's own (a mantle's).
            hands.StopSlotAnimation(BLEND_S, SLOT)
    except Exception as exc:
        _fail(exc)


def reset() -> None:
    """The character changed or the climb was switched off: the old arms and their montage went with it."""
    global _playing, _broken, _announced
    _playing = _broken = _announced = False
    climb_body.reset()


def update_wall(wall: object) -> None:
    climb_body.update_wall(wall)


def _fail(exc: Exception) -> None:
    global _playing, _broken
    _playing, _broken = False, True
    report.error_once("climb_animation", f"climb animation switched off after an error: {exc!r}")
