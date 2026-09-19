"""The ground slam and the landing slide (spec, section 2.3): a tap dashes, a hold slides at landing above the minimum
speed, crouch and jump together slam.

Each frame follows the game's key list, turns the requests of air_keys into game calls, and watches for the landing.
The keys are released at every character change and bound again from the game's key list the next frame; the list is
then read again every second, and the keys bound again when it changed, unless it lists no crouch key at all.
Switched off, the keys are released and the game gets its own crouch back, hold slam included.

One switch for both, deliberately (Kevin, 2026-09-18). Every mod of this pack is one movement, but these two share the
crouch key being blocked, and that block is what removes the game's own slam on a held crouch. Two switches would
allow a state where the block stays on while the player asked for neither: they would lose the held-crouch slam and
have no way to tell why. Turned off, the key goes back to the game and the game's own slam returns with it.
"""

from typing import Any

from . import air_actions, air_bindings, air_keys, game, report, speed_order

# Once a second, not every frame: the list holds every mapping of the player. Read only at a character change, it
# missed the gamepad's crouch key at a vehicle exit, and that key stayed unbound until the next level (2026-09-18).
KEYS_CHECK_NS = 1_000_000_000

_was_in_air = False
_air_speed = 0.0
_next_keys_ns = 0


def reset() -> None:
    global _was_in_air, _air_speed, _next_keys_ns
    # So that the next frame reads the key list again: the new character may come with other keys.
    air_bindings.unbind()
    air_keys.reset()
    air_actions.forget()
    _was_in_air, _air_speed, _next_keys_ns = False, 0.0, 0


def _follow_keys(now_ns: int) -> None:
    """Binds the keys the game lists, and binds them again when the list changes."""
    global _next_keys_ns
    if now_ns < _next_keys_ns:
        return
    _next_keys_ns = now_ns + KEYS_CHECK_NS
    # Never between a press and its release: the release must reach the key that saw the press.
    if air_keys.is_held():
        return
    mappings = game.input_mappings()
    if air_bindings.is_bound():
        # A list without any crouch key while bound is the vehicle's: the game switches keys a moment before the
        # character leaves (2026-09-19). Kept bound, the character change releases them; reported, it was a false error.
        if air_bindings.matches(mappings) or not air_bindings.keys_for(mappings, air_bindings.CROUCH_ACTIONS):
            return
        air_bindings.unbind()
    if not air_bindings.bind(mappings):
        report.error_once("air_crouch:keys", "no crouch key in the game's input list; looked for again every second")


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
    _follow_keys(now_ns)
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
