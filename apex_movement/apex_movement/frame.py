"""Runs each switched-on movement once per frame, on the player only.

A movement that raises is switched off alone and reported once: one broken movement must not take the others down.
A switch turned off in the menu stops its movement at the next frame the player has a character, which puts its
values back; turned off at the main menu, that is the first frame of the next game.
"""

import time
from typing import Any

from mods_base import hook
from unrealsdk.hooks import Type

from . import game, ownership, report, settings, walk_key

_movements: list[tuple[str, Any, Any]] = []
_active: set[str] = set()
_failed: set[str] = set()
_camera: Any = None
_camera_in_game = False
# A line each time the player changes, bounded per switch-on: session 6 (2026-09-18) stayed silent a whole game until
# the mod was switched off and on, and no line said whether the player had been found at all.
MAX_PLAYER_LINES = 100
_player_lines = 0


def _name(obj: Any) -> str:
    return "none" if obj is None else str(getattr(obj, "Name", "?"))


def register(name: str, movement: Any, *switches: Any) -> None:
    """A movement module offers update(character, now_ns), stop(character) and reset().

    It runs while every one of its switches is on, and stops at the next frame as soon as one goes off. A module of a
    movement that also has its own option takes both: the movement's switch, so turning the movement off turns it off
    too, and its own (2026-09-18). No switch at all means always on, and movements.py carries the reason.
    """
    _movements.append((name, switches, movement))


def set_camera(camera: Any) -> None:
    global _camera, _camera_in_game
    _camera = camera
    if camera is None:
        _camera_in_game = False


def _update_camera(now_ns: int) -> None:
    if _camera is None:
        return
    try:
        _camera.on_frame(now_ns)
    except Exception as exc:
        report.error_once("camera", f"camera update skipped after an error: {exc!r}")


def _stop(name: str, movement: Any, character: Any) -> None:
    try:
        movement.stop(character)
    except Exception as exc:
        # Left running, so that it is stopped again at the next frame or the next switch-off: a stop that failed could
        # leave a key blocked while the menu shows the move off (review, 2026-09-19).
        report.error_once(f"{name}:stop", f"{name} could not stop cleanly: {exc!r}")
        return
    _active.discard(name)


_CHANGE_TEXT = {
    game.CHARACTER: "character changed",
    game.ANIMATION: "animation changed",
    game.AWAY: "left the character, or came back to the same one",
}


def _tell_player(change: str) -> None:
    global _player_lines
    if _player_lines < MAX_PLAYER_LINES:
        _player_lines += 1
        report.note(f"player {_CHANGE_TEXT[change]}, character={_name(game.character())}"
                    f" animation={_name(game.anim())}")


def on_frame(obj: Any, now_ns: int) -> None:
    global _camera_in_game
    try:
        change = game.refresh(now_ns)
    except Exception as exc:
        # Skipped rather than raised out of the hook, which would repeat the error at every animation update.
        report.error_once("frame:refresh", f"the player could not be looked up, frame skipped: {exc!r}")
        return
    if change:
        _tell_player(change)
    if change in (game.CHARACTER, game.AWAY):
        # A vehicle keeps the same character and its written values, but no transient action may cross the time away:
        # carrying a slide model through a ride resumed it with an old timer and zero speed (2026-09-23).
        if change == game.CHARACTER:
            ownership.forget_character()
        for name, _, movement in _movements:
            try:
                movement.reset()
            except Exception as exc:
                report.error_once(f"{name}:reset", f"{name} could not forget the old character: {exc!r}")
    character = game.character()
    if character is None:
        if _camera_in_game:
            _camera_in_game = False
            _update_camera(now_ns)
        return
    if obj != game.anim():
        return
    _camera_in_game = True
    _update_camera(now_ns)
    for line in settings.keep_in_bounds(walk_key.speed):
        report.warning(line)
    for name, switches, movement in _movements:
        if name in _failed:
            continue
        if not all(switch.value for switch in switches):
            if name in _active:
                _stop(name, movement, character)
            continue
        _active.add(name)
        try:
            movement.update(character, now_ns)
        except Exception as exc:
            _failed.add(name)
            report.error_once(name, f"{name} switched off after an error: {exc!r}")
            _stop(name, movement, character)


def stop_all() -> list[str]:
    global _player_lines
    _player_lines = 0
    # Looked up now rather than up to a second ago: switched off at the title screen, the character is gone, and its
    # values are forgotten instead of written into it (review, 2026-09-19). A character merely put aside by a
    # vehicle is still alive, and its values are put back into it (2026-09-20).
    game.refresh(time.perf_counter_ns(), at_once=True)
    if game.last_character() is None:
        ownership.forget_character()
    character = game.character()
    for name, _, movement in _movements:
        if name in _active:
            _stop(name, movement, character)
    failures = ownership.restore_all()
    _failed.clear()
    game.forget()
    return failures


# The identifier carries the package's own name: two separate files installed side by side each hold their own hook,
# and one registered under a name already taken would replace the other's (2026-09-18).
@hook("/Script/Engine.AnimInstance:BlueprintUpdateAnimation", Type.POST, hook_identifier=f"{__package__}:frame")
def tick(obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    now_ns = time.perf_counter_ns()
    on_frame(obj, now_ns)
