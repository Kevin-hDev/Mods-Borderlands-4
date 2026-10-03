"""The attack, frame by frame: while the key is held and energy is left, the beam is on and hits what it is on.

The one place that decides: the key says what the player wants, the reserve says whether he may, and this module
raises the hand, lights the beam, moves it, hits on its own beat and switches everything off. An error in a frame
ends the shot: nothing is left lit and the hand comes down. A part that fails on its own (the beam, the pose, the
hand, the level, the hit) says so once and leaves the rest of the shot going.

What the beam is on is the aim's enemy, or the one caught beside the aim (catch.py), or the one the lock holds while
the aim strays (lock.py); the bounce adds a second enemy, hit on the same beat for the same amount (bounce.py). All
three are the player's to switch off.
"""

import sys
from typing import Any

from . import aim, bar, beam, bounce, catch, damage, foes, gesture, hand, keys, lock, player, report, reserve
from . import settings, shot_report, strength, view
from .slider_values import bounded

# A frame longer than this is a hitch: it drains and refills as this much, no more.
MAX_FRAME_S = 0.25
# No frame for this long: a pause, a menu or a loading stopped the game's beat, and the key's release may have gone
# unseen meanwhile (the heirloom's key_press.py guards its hold the same way). The shot ends and the key is
# forgotten: without it the beam's hits went on by themselves after a loading, with no beam and no hand (audit of
# 2026-10-01).
GAP_S = 0.5
HIT_S = 1.0 / settings.HITS_PER_SECOND
# Frame times added up fall a hair short of the beat they make.
ROUNDING_S = 1e-9

energy = reserve.Reserve()
_firing = False
_last_s: float | None = None
# The beam's time not yet paid in hits. Kept from one shot to the next: a key tapped earns its hits as a key held
# does, at the price in energy a key held pays. Each new shot used to hit at once: ten taps a second hit four times
# as often as the key held, for the same energy (audit of 2026-10-01).
_unpaid_s = 0.0
# One line of the log per shot says who was hit first and how far: the proof that far targets are reached.
_hit_said = False


def stop() -> None:
    """Ends the shot and forgets the key; called when the mod is switched off and after an error in a frame."""
    global _firing, _last_s, _unpaid_s
    _firing = False
    _last_s = None
    _unpaid_s = 0.0
    keys.release()
    _put_out()


def _put_out() -> None:
    """Everything a shot lit or held is given back: its beam, the bounce's, the enemy locked, the hand."""
    beam.off()
    bounce.forget()
    lock.forget()
    gesture.lower()


def _fire(pc: Any, character: Any, passed: float) -> None:
    global _firing, _unpaid_s, _hit_said
    starting = not _firing
    if starting:
        _firing, _hit_said = True, False
        hand.forget()
        shot_report.begin()
    locking = settings.lock.value is True
    aimed = aim.look(pc, character, settings.REACH)
    # The catch looks beside the aim for an enemy: with one under it or one locked there is nobody to look for.
    if aimed.enemy is None and not lock.held():
        aimed = catch.near(pc, character, aimed, bounded(settings.width), settings.REACH)
    first = (lock.follow(pc, character, aimed, passed, bounded(settings.lock_delay), bounded(settings.lock_angle))
             if locking else lock.plain(aimed))
    end = first.point if first is not None else aimed.anchor
    shot_report.frame(aimed, first, passed)
    damage_type, effect = settings.chosen()
    if starting:
        # Lit once per shot: a beam the game refuses is not asked for again at every frame, and the hits go on.
        raised = gesture.raise_hand(character)
        beam.light(character, effect, hand.spot(pc, character), end)
        # The element, not its damage type: two elements can share one (the two white candidates did, and the log
        # of 2026-10-01 could not tell them apart).
        report.note(f"beam on, {settings.element_name()}, level {player.level(pc)}, "
                    f"hand {'raised on ' + ' and '.join(raised) if raised else 'down'}, "
                    f"{'third' if view.third_person(pc, character) else 'first'} person"
                    f"{', no damage: the game refused a hit' if damage.refused() else ''}")
    else:
        beam.follow(hand.spot(pc, character), end)
    second = bounce.follow(character, first, effect) if settings.bounce.value is True else bounce.forget()
    _unpaid_s += passed
    if _unpaid_s >= HIT_S - ROUNDING_S:
        # One hit a frame at most: a frame longer than the beat does not hit twice.
        _unpaid_s = min(max(_unpaid_s - HIT_S, 0.0), HIT_S)
        if first is not None:
            amount = strength.per_hit(bounded(settings.damage), player.level(pc), settings.HITS_PER_SECOND)
            landed = damage.hit(character, first.enemy, first.hit, amount, damage_type)
            # Only a hit the game took: a line of this log is a proof.
            if landed and not _hit_said:
                _hit_said = True
                report.note(f"hit {first.species} at {first.distance / 100:.0f} m")
            if second is not None:
                damage.hit(character, second.enemy, second.hit, amount, damage_type)


def _window_open() -> bool:
    """Whether the mod's window is open. Its module is asked only once something has loaded it: the attack must
    not need the window to load (panel_open.py keeps the SDK's menu when the window cannot be had)."""
    window = sys.modules.get(f"{__package__}.control_window")
    return window is not None and window.active()


def _cease() -> None:
    global _firing
    if _firing:
        _firing = False
        seen = beam.state()
        _put_out()
        report.note(f"beam off, energy {energy.left:.0f}, {seen}")
        report.note(shot_report.line())


def on_frame(now_s: float) -> None:
    global _last_s
    gap = 0.0 if _last_s is None else max(now_s - _last_s, 0.0)
    _last_s = now_s
    passed = min(gap, MAX_FRAME_S)
    foes.tick(passed)
    try:
        if gap > GAP_S and (_firing or keys.held()):
            report.note(f"no frame for {gap:.1f} s: the shot ends and the key is forgotten")
            _cease()
            keys.release()
        pc, character = player.current()
        # The window takes the keyboard: a key held when it opens may never be seen released.
        if character is None or _window_open():
            keys.release()
        held = keys.held()
        # Each slider is read within its bounds here, whatever wrote it: the SDK's own console menu takes any
        # number the player types (review of 2026-10-02).
        drain = bounded(settings.drain)
        # A shot begins only if the reserve can pay for one hit.
        if character is not None and held and energy.can_fire(0.0 if _firing else drain * HIT_S):
            _fire(pc, character, passed)
            energy.spend(passed, drain)
            if not energy.can_fire():
                _cease()
        else:
            _cease()
            energy.rest(passed, bounded(settings.regen), bounded(settings.regen_delay), held)
    except Exception as error:
        report.error_once("frame", f"the shot stopped after an error: {error!r}")
        stop()
    if settings.show_bar.value is True:
        bar.tell(energy.left, reserve.MAXIMUM, settings.element_name())
    else:
        bar.hide()
