"""Wall climb (phase 2 spec): jump at a wall with the stick and the camera toward it, and climb up it.

Measured on 2026-09-17 (M1): a vertical speed written every frame holds in the air (500 written, 490 a second kept),
and the game's own mantle took over at the top of a crate three times out of four while the push went on; the one miss
was a push stopped as soon as nothing was left at head level. So a climb pushes up, and a little into the wall, until
the game mantles or climb_rules ends it. The speed is written each frame of a climb only.

The arms play the game's own climbing animation during a climb (climb_animation, session G).

The game mantles an ordinary ledge only with the jump key held for its MinPassiveMantleButtonHoldDuration, 0.075 s;
at 0 it mantled without the key (session C, 2026-09-17). Kevin chose to keep 0 everywhere while the wall climb is on,
as Apex mantles on its own, so it is written once and put back when the climb is switched off. A climb from the foot of
a ledge still did not mantle without Croix (session D); pressing Croix for one frame while the game allows a mantle did,
6 times out of 6 (session H), so a climb presses it there (jump_press). Kevin's choice: at the top, the player hoists by
itself.

A climb also counts as a landing for the jumps: air_jumps gives both back when it starts, so the player jumps from the
wall and still has the double jump, in the climb or in the fall that follows (Kevin, 0.8.6 session).

A climb follows the move stick along the wall, including fully sideways at 90 degrees (Kevin, 2026-09-24). Vertical,
diagonal and horizontal climbs spend the same path-distance budget, so no direction grants more travel than another.
"""

from typing import Any

from unrealsdk import unreal

from . import (climb_aim, climb_animation, climb_refusal, climb_rules, climber, game, guest_trust, jump_press,
               ownership, report, wall_sense)

NS_PER_S = climber.NS_PER_S
HOLD_FIELD = "MinPassiveMantleButtonHoldDuration"
HOLD_KEY = f"controller.{HOLD_FIELD}"
GUEST_MEMO = "climb"
# A guest's climber left this long without a frame (the climb switched off and on, a pause) starts over rather than
# carry a climb begun long ago.
GUEST_STALE_NS = NS_PER_S
# One line per start and end of a guest's climb, bounded per switch-on: a guest climbing all game cannot fill the log.
MAX_GUEST_LINES = 100
GUEST_TRUST_MEMO = "climb trust"
# One line per climb that presses Croix, not one per frame of the window.
_pressed = False
_guest_lines = 0

_climber = climber.Climber(lambda text: report.note(text))
# Read by Apex Grapple (apex_grapple/coordination.py), published 1.0.9 included: its rope yields while
# `wall_climb._rules.start` is set. Moved into the climber on 2026-10-17, the name went, and every rope yielded at once
# (Kevin: « pourquoi apex grapple fonctionne plus ? »). Kept here, the player's climber's own rules.
_rules = _climber.rules


def reset() -> None:
    global _climber, _rules
    _climber = climber.Climber(lambda text: report.note(text))
    _rules = _climber.rules
    wall_sense.reset()
    climb_refusal.reset()
    climb_animation.reset()


def _hold_of(pointer: Any) -> float:
    return float(getattr(ownership.loaded(pointer()), HOLD_FIELD))


def _put_hold(pointer: Any, value: float) -> None:
    # Gone after a return to the title screen: writing into it could bring the game down (review, 2026-09-19), and the
    # next controller starts from the game's own hold anyway. Said as unloaded rather than silently: a put that
    # changes nothing must not read as a value given back (2026-09-20).
    setattr(ownership.loaded(pointer()), HOLD_FIELD, value)


def _mantle_without_jump_key() -> None:
    pc = game.controller()
    if pc is None or float(getattr(pc, HOLD_FIELD)) == 0.0:
        return
    # Asset scope: the controller outlives the character, so its value is put back even after a level change.
    pointer = unreal.WeakPointer(pc)
    ownership.write(HOLD_KEY, ownership.ASSET, lambda: _hold_of(pointer),
                    lambda value: _put_hold(pointer, value), 0.0)
    report.note("mantle without the jump key on")


def update(character: Any, now_ns: int) -> None:
    global _pressed
    _mantle_without_jump_key()
    moment, limits, step = _climber.step(character, now_ns, game.stick_direction(character))
    wall = moment.wall
    if step.event == "start":
        _pressed = False
        climb_refusal.started()
        report.note(f"wall climb start distance={wall.distance:.0f} "
                    f"stick_deg={climb_aim.angle_to_wall(moment.stick_x, moment.stick_y, wall):.0f} "
                    f"view_deg={climb_aim.view_angle(moment.view_yaw, wall):.0f} z={moment.z:.0f}")
        climb_animation.start(climb_rules.longest_climb_ns(limits) / NS_PER_S, wall)
    elif step.event:
        report.note(f"wall climb end reason={step.event} rise={step.rise:.0f} distance={step.distance:.0f} "
                    f"ms={step.ms} lean={_climber.max_lean:.0f}")
        climb_animation.stop()
    if step.climbing:
        # The trace can move to another face on an irregular wall; the body follows the wall used by this frame.
        climb_animation.update_wall(wall)
        _hoist(character.CharacterMovement)
    elif not step.event:
        # Not on the frame a climb ends: the wait it just set would be told as a refusal of the climb that succeeded.
        climb_refusal.note(_climber.rules.start_refusal(moment, limits), moment, limits)
    _climber.after_rules(character, now_ns)


def for_guest(guest: Any) -> dict[str, Any]:
    """On a co-op host, climbs each guest as the guest's own game does, from what the host knows of them: their
    acceleration for the stick, their controller's heading, their jumps (verified readable on the host, 2026-10-17).
    The speed is written straight into the guest's character every frame of a climb, like the player's: a speed, not
    a value to give back. From the climb to the landing after it, the host takes the guest's place (guest_trust):
    it starts a guest's climb late and ends it on its own judgement, and corrected the guest all along
    (docs/coop/2026-10-17-saccades-restantes.md, trials 5 and 6). Not played for a guest: the arms' animation, the
    hoist press, which the guest's own game makes, and the refusal lines."""
    global _guest_lines
    held = guest.memo.get(GUEST_MEMO)
    if held is None or guest.now_ns - held.last_ns > GUEST_STALE_NS:
        held = guest.memo[GUEST_MEMO] = climber.Climber(lambda text: None)
    character = guest.character
    moment, _limits, step = held.step(character, guest.now_ns, climber.remote_stick(character))
    if step.event and _guest_lines < MAX_GUEST_LINES:
        _guest_lines += 1
        name = str(getattr(character, "Name", "?"))
        detail = (f"z={moment.z:.0f}" if step.event == "start" else
                  f"rise={step.rise:.0f} distance={step.distance:.0f} ms={step.ms}")
        what = "start" if step.event == "start" else f"end reason={step.event}"
        report.note(f"co-op guest {name}: wall climb {what} {detail}")
    held.after_rules(character, guest.now_ns)
    return guest_trust.until_landing(guest, GUEST_TRUST_MEMO, step.climbing)


def _hoist(movement: Any) -> None:
    """Presses Croix while the game allows a mantle; a failure is reported once and the climb goes on."""
    global _pressed
    try:
        if not game.can_mantle(movement):
            return
        if not jump_press.press():
            report.error_once("jump_press", "hoist unavailable: the game's jump input was not found")
            return
    except Exception as exc:
        report.error_once("jump_press:error", f"hoist failed: {exc!r}")
        return
    if not _pressed:
        _pressed = True
        report.note("wall climb hoist: jump pressed while the game allows a mantle")


def stop(character: Any) -> None:
    global _guest_lines
    _guest_lines = 0
    if _climber.rules.start is not None:
        # Without it, a climb switched off halfway has a start line and no end in the log.
        report.note("wall climb end reason=switched_off")
    climb_animation.stop()
    jump_press.forget()
    reset()
    ownership.restore(HOLD_KEY)
    report.note("wall climb off, mantle needs the jump key again")
