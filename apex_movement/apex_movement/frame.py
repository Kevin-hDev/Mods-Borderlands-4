"""Runs each switched-on movement once per frame, on the player only.

A movement that raises is switched off alone and reported once: one broken movement must not take the others down.
A switch turned off in the menu stops its movement at the next frame the player has a character, which puts its
values back; turned off at the main menu, that is the first frame of the next game.
"""

import time
from typing import Any

from mods_base import hook
from unrealsdk.hooks import Type

from . import game, ownership, report, settings

_movements: list[tuple[str, Any, Any]] = []
_active: set[str] = set()
_failed: set[str] = set()
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


def _stop(name: str, movement: Any, character: Any) -> None:
    try:
        movement.stop(character)
    except Exception as exc:
        # Left running, so that it is stopped again at the next frame or the next switch-off: a stop that failed could
        # leave a key blocked while the menu shows the move off (review, 2026-09-19).
        report.error_once(f"{name}:stop", f"{name} could not stop cleanly: {exc!r}")
        return
    _active.discard(name)


def _tell_player(change: str) -> None:
    global _player_lines
    if _player_lines < MAX_PLAYER_LINES:
        _player_lines += 1
        report.note(f"player {change} changed, character={_name(game.character())} animation={_name(game.anim())}")


def on_frame(obj: Any, now_ns: int) -> None:
    try:
        change = game.refresh(now_ns)
    except Exception as exc:
        # Skipped rather than raised out of the hook, which would repeat the error at every animation update.
        report.error_once("frame:refresh", f"the player could not be looked up, frame skipped: {exc!r}")
        return
    if change:
        _tell_player(change)
    if change == game.CHARACTER:
        # The old character's values went with it; only the movements' own memory needs clearing. The running set
        # is kept on purpose: the slide and dash assets, the jump definitions and the key binds outlive the
        # character, so a switch turned off before the next character arrives must still stop its movement then.
        # Clearing it here left them written for good (review, 2026-09-18).
        ownership.forget_character()
        for name, _, movement in _movements:
            try:
                movement.reset()
            except Exception as exc:
                report.error_once(f"{name}:reset", f"{name} could not forget the old character: {exc!r}")
    character = game.character()
    if character is None or obj != game.anim():
        return
    for line in settings.keep_in_bounds():
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
    # values are forgotten instead of written into it (review, 2026-09-19).
    if game.refresh(time.perf_counter_ns(), at_once=True) == game.CHARACTER:
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
    on_frame(obj, time.perf_counter_ns())
