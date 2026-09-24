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

from . import (air_jumps, climb_aim, climb_animation, climb_refusal, climb_rules, game, jump_press,
               ownership, report, settings, wall_choice, wall_sense)

# The measure's lean into the wall, which kept the character touching it all the way up.
INTO_WALL = 100.0
NS_PER_S = 1_000_000_000
HOLD_FIELD = "MinPassiveMantleButtonHoldDuration"
HOLD_KEY = f"controller.{HOLD_FIELD}"
# One line per climb that presses Croix, not one per frame of the window.
_pressed = False
# The fullest lean of the climb under way, told at its end: the only way a log shows a diagonal was really climbed.
_max_lean = 0.0

_rules = climb_rules.Rules()


def reset() -> None:
    global _rules, _max_lean
    _rules = climb_rules.Rules()
    _max_lean = 0.0
    wall_sense.reset()
    climb_refusal.reset()
    climb_animation.reset()
    air_jumps.reset()


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


def _limits(character: Any) -> climb_rules.Limits:
    distance = 2.0 * game.half_height(character) * float(settings.climb_height.value) / 100.0
    return climb_rules.Limits(distance=distance, delay_ns=int(float(settings.reclimb_delay.value) * NS_PER_S),
                              lean_deg=float(settings.climb_lean.value), speed=float(settings.climb_speed.value))


def _moment(character: Any, now_ns: int) -> climb_rules.Moment:
    movement = character.CharacterMovement
    in_air = game.is_in_air(movement)
    yaw = game.view_yaw(character)
    stick_x, stick_y = game.stick_direction(character)
    # Traces in the air only: on the ground no climb can start or go on.
    walls = (wall_sense.walls_ahead(character, yaw, game.half_height(character))
             if in_air and yaw is not None else [])
    high = [wall for wall, share in zip(walls, wall_sense.hit_heights(walls)) if share >= climb_aim.HIGH_FROM]
    location = character.K2_GetActorLocation()
    return climb_rules.Moment(
        now_ns=now_ns, in_air=in_air, on_ground=game.is_on_ground(movement),
        game_move=game.in_controlled_move(movement), mantling=game.is_mantling(movement),
        near_game_climb=game.is_near_game_climb(movement),
        x=float(location.X), y=float(location.Y), z=float(location.Z),
        jumps=game.jump_count(character), stick_x=stick_x, stick_y=stick_y, view_yaw=yaw,
        wall=wall_choice.best_wall(walls), hits=len(walls),
        high_wall=wall_choice.best_wall(high) is not None,
    )


def update(character: Any, now_ns: int) -> None:
    global _pressed, _max_lean
    _mantle_without_jump_key()
    moment = _moment(character, now_ns)
    limits = _limits(character)
    step = _rules.step(moment, limits)
    wall = moment.wall
    speed = limits.speed
    if step.event == "start":
        _pressed, _max_lean = False, 0.0
        climb_refusal.started()
        air_jumps.climb_started(character, now_ns)
        report.note(f"wall climb start distance={wall.distance:.0f} "
                    f"stick_deg={climb_aim.angle_to_wall(moment.stick_x, moment.stick_y, wall):.0f} "
                    f"view_deg={climb_aim.view_angle(moment.view_yaw, wall):.0f} z={moment.z:.0f}")
        climb_animation.start(climb_rules.longest_climb_ns(limits) / NS_PER_S, wall)
    elif step.event:
        report.note(f"wall climb end reason={step.event} rise={step.rise:.0f} distance={step.distance:.0f} "
                    f"ms={step.ms} lean={_max_lean:.0f}")
        climb_animation.stop()
    if step.climbing:
        # The trace can move to another face on an irregular wall; the body follows the wall used by this frame.
        climb_animation.update_wall(wall)
        lean = climb_aim.lean_degrees(moment.stick_x, moment.stick_y, wall, limits.lean_deg)
        _max_lean = max(_max_lean, abs(lean))
        side_x, side_y, up = climb_aim.climb_direction(lean, wall)
        # Never slower than the rise already under way: a climb starting on the frame a jump leaves the ground used to
        # replace 912 with the climb speed, which turned a sprint jump into a hop (Kevin, 2026-09-17).
        rise = max(up * speed, float(character.CharacterMovement.Velocity.Z))
        game.set_velocity(character.CharacterMovement, wall.into_x * INTO_WALL + side_x * speed,
                          wall.into_y * INTO_WALL + side_y * speed, rise)
        _hoist(character.CharacterMovement)
    elif not step.event:
        # Not on the frame a climb ends: the wait it just set would be told as a refusal of the climb that succeeded.
        climb_refusal.note(_rules.start_refusal(moment, limits), moment, limits)
    # After the rules read the jump count: a jump given back before them would hide the jump that ends a climb.
    given = air_jumps.update(character, now_ns)
    if given is not None:
        _rules.jumps_given_back(given)


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
    if _rules.start is not None:
        # Without it, a climb switched off halfway has a start line and no end in the log.
        report.note("wall climb end reason=switched_off")
    climb_animation.stop()
    jump_press.forget()
    reset()
    ownership.restore(HOLD_KEY)
    report.note("wall climb off, mantle needs the jump key again")
