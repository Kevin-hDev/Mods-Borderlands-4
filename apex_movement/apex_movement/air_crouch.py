"""The ground slam and the landing slide (spec, section 2.3): a tap dashes, a hold slides at landing above the minimum
speed, crouch and jump together slam.

Each frame binds the keys when they are not bound, turns the requests of air_keys into game calls, and watches for the
landing. The keys are released at every character change and bound again from the game's key list the next frame.
Switched off, the keys are released and the game gets its own crouch back, hold slam included.

One switch for both, deliberately (Kevin, 2026-09-18). Every mod of this pack is one movement, but these two share the
crouch key being blocked, and that block is what removes the game's own slam on a held crouch. Two switches would
allow a state where the block stays on while the player asked for neither: they would lose the held-crouch slam and
have no way to tell why. Turned off, the key goes back to the game and the game's own slam returns with it.
"""

from typing import Any

from . import air_actions, air_bindings, air_keys, game, report, speed_order

_was_in_air = False
_air_speed = 0.0
_bind_refused = False


def reset() -> None:
    global _was_in_air, _air_speed, _bind_refused
    # So that the next frame reads the key list again: a crouch key changed in the game's options replaces the old one.
    air_bindings.unbind()
    air_keys.reset()
    air_actions.forget()
    _was_in_air, _air_speed, _bind_refused = False, 0.0, False


def _bind() -> None:
    global _bind_refused
    if air_bindings.bind(game.input_mappings()):
        return
    # Tried again after the next level load only: reading the key list every frame would cost for nothing.
    _bind_refused = True
    report.error_once("air_crouch:keys", "no crouch key in the game's input list; air crouch waits for the next level")


def _landed(character: Any, now_ns: int) -> None:
    if not air_keys.is_held():
        return
    minimum = speed_order.speeds().landing_slide_min
    if _air_speed < minimum:
        report.note(f"landing held speed_in={_air_speed:.0f} below min={minimum:.0f}: no slide")
        return
    air_actions.start_slide(character, now_ns, _air_speed, minimum)


def update(character: Any, now_ns: int) -> None:
    global _was_in_air, _air_speed
    if not air_bindings.is_bound() and not _bind_refused:
        _bind()
    for kind in air_keys.due_requests(now_ns):
        if kind == "dash":
            air_actions.start_dash(character, now_ns)
        elif kind == "slam":
            air_actions.slam(character)
    movement = character.CharacterMovement
    in_air = game.is_in_air(movement)
    if in_air:
        # The last speed in the air is the arrival speed the minimum is compared with, in real units (decision 8).
        _air_speed = game.horizontal_speed(movement)
    elif _was_in_air and game.is_on_ground(movement):
        _landed(character, now_ns)
    elif _was_in_air and air_keys.is_held():
        # Left the air for another mode than walking, a mantle for one: no landing slide. Logged so that a chained
        # slide jump that did not slide can be told apart from a released key (0.8.4, two such misses unexplained).
        report.note(f"landing held into {game.movement_mode(movement)}: no slide")
    _was_in_air = in_air
    air_actions.update(character, now_ns)


def stop(character: Any) -> None:
    air_actions.stop(character)
    reset()
