"""One SDK hook on the game's animation update for every beat of this copy of the package.

The game calls BlueprintUpdateAnimation once per animated character and per image, 447 to 1 358 times a second with
eight companions and a Horde (trial 219 of docs/renforts), and each Python hook on it costs the SDK about 2.5 µs before
any of our code runs (trial 40 of docs/RUN). It Follows held up to four at once: its mode's beat (frame.py), the
enemies' dodges (normal/enemy_time.py), the team (companions/team.py) and the strays' watch (companions/strays.py).
This front gives the SDK one hook and calls each beat in the order it was set (audit of 24 October 2026, C2), as the
camera runtime's frame_hooks.py has done for its units since the same day (vérifié en jeu, docs/performance). The
Horde's start (start_cover.py, start_trip.py) keeps hooks of its own: they last a few seconds under the black screen.

A beat set during a call runs from the next one; a beat removed during a call runs no more. The SDK's hook is set when
the first beat is, and removed once none is left: never during a call on that thread, but at its end, so that a beat
that stops and another that starts within one call (a team stopping, its strays' watch starting) leave the SDK's hook
as it was. Each beat keeps its own guard of the game's thread (game_thread.py, decision 62). A beat that raises is
said once by its name and its error's kind, and the others still run, as the SDK did for a hook of their own. Named
after the mod this copy ships in, so that two mods carrying the package never take each other's hook.
"""

import threading
from typing import Any, Callable

from mods_base import hook
from unrealsdk.hooks import Type

from . import report

HOOK = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
IDENTIFIER = f"{__package__.split('.')[0]}:animation"
MAX_TEXT = 120
# The beats' errors said, each once: a handful in practice; past this, new ones are not said.
MAX_SAID = 32

_beats: dict[str, Callable[..., Any]] = {}
_hook: list[Any] = [None]
_said: set[str] = set()
# How deep in a call each thread is: the SDK's hook is removed only outside one.
_calling = threading.local()


class Beat:
    """One beat's place on the front, taken by enable() and given up by disable(), as a hook of mods_base's is."""

    def __init__(self, identifier: str, callback: Callable[..., Any]) -> None:
        self.identifier, self.callback = identifier, callback

    def enable(self) -> None:
        if _hook[0] is None:
            made = hook(HOOK, Type.POST, hook_identifier=IDENTIFIER)(_call)
            made.enable()
            _hook[0] = made
        _beats[self.identifier] = self.callback

    def disable(self) -> None:
        if _beats.get(self.identifier) is self.callback:
            del _beats[self.identifier]
        if not _beats and _depth() == 0:
            _unhook()


def beat(identifier: str, callback: Callable[..., Any]) -> Beat:
    """callback(obj, args, ret, func) called after each animation update, under that name, while enabled."""
    return Beat(identifier, callback)


def beats() -> dict[str, Callable[..., Any]]:
    """The beats set, by name, in their order."""
    return dict(_beats)


def hooked() -> bool:
    """Whether the SDK's hook is set."""
    return _hook[0] is not None


def _depth() -> int:
    return getattr(_calling, "depth", 0)


def _call(obj: Any = None, args: Any = None, ret: Any = None, func: Any = None) -> None:
    _calling.depth = _depth() + 1
    try:
        for identifier, callback in tuple(_beats.items()):
            if _beats.get(identifier) is not callback:
                continue
            try:
                callback(obj, args, ret, func)
            except Exception as error:
                _say(identifier, error)
    finally:
        _calling.depth -= 1
        if not _beats and _calling.depth == 0:
            _unhook()


def _say(identifier: str, error: Exception) -> None:
    key = f"{identifier}:{type(error).__name__}"
    if key in _said or len(_said) >= MAX_SAID:
        return
    _said.add(key)
    report.note("animation_beat_failed", beat=identifier, error=f"{type(error).__name__}:{str(error)[:MAX_TEXT]}")


def _unhook() -> None:
    active, _hook[0] = _hook[0], None
    if active is not None:
        active.disable()
