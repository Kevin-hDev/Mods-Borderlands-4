"""The hunter change asked in a game (conception-idee-2.md, « Quand le mod écrit », validated by Kevin on 2026-09-28).
The request is kept in memory only: a crash on the way changes nothing. At the next tick of its own clock, once the
window is gone, the engine is asked to take the player back to the main menu (GameModeBase:ReturnToMainMenuHost on the
one live game mode, essai 35). The game saves the game, then writes it again from memory just before the title screen
is ready (essais 34 and 35): the mod waits for ServerNotifyCharacterReadyForGameplay at the title screen with the
request's game selected, then for its save to stay unchanged SETTLE_S, and only then changes it (switch.py). Past
AFTER_SIGNAL_S after the signal or AFTER_CALL_S after the call it gives up, with a game loading or loaded meanwhile it
ends as LOADED, and both write nothing. An error inside the change itself ends as ERROR: the save or the trees may have
changed.

An end of the change itself is kept with the stamp of the save as the change left it, so that the page can tell the
game wrote the save since (it does when the player leaves the game's selection, loads it or clicks Continue, essais 8,
34 and 37): the end's next step is then followed or overtaken, and the page drops it. Leave's own ends carry none.

Its clock is a Windows timer on the game thread (control_timer_native.py), the one the window polls with, seen running
at the title screen (essais 33 and 34); the frame hook is not known to run there. One request at a time. Every log line
carries the request's operation number, never a path nor an account number.
"""

import secrets
import time
from dataclasses import dataclass
from itertools import islice
from types import SimpleNamespace
from typing import Any

import unrealsdk
from mods_base import get_pc, hook
from unrealsdk.hooks import Type

from . import control_timer_native, hunters, report, save_places, switch
from .game_id import PATTERN as ID_PATTERN, game_id

READY_PATH = "/Script/OakGame.OakPlayerController:ServerNotifyCharacterReadyForGameplay"
SETTLE_S = 2.0
AFTER_SIGNAL_S = 20.0
AFTER_CALL_S = 60.0
# Bounds the walk through the game's objects: one live mode is expected, a few more already refuse.
MAX_MODES = 8
NO_RETURN, GAVE_UP, LOADED, ERROR = "no_return", "gave_up", "loaded", "error"
IDLE, ASKED, RETURNING, SIGNALLED, SETTLING, WRITING = "idle", "asked", "returning", "signalled", "settling", "writing"
WAITING = (RETURNING, SIGNALLED, SETTLING)

now = time.perf_counter
new_timer = control_timer_native.NativeTimer


@dataclass(frozen=True)
class Result:
    game: str
    current: str
    wanted: str
    outcome: switch.Outcome
    # (st_mtime_ns, st_size) of the save as switch.change left it; None for leave's own ends (no_return, gave_up,
    # loaded), which changed nothing.
    stamp: tuple[int, int] | None


STATE = SimpleNamespace(phase=IDLE, request=None, called_at=0.0, signal_at=0.0, save=None, stamp=None,
                        stable_since=0.0, said_other=False, last=None)
_timer: Any = None


def live_modes() -> list[Any]:
    modes = (mode for mode in unrealsdk.find_all("OakGameMode", exact=False)
             if not str(mode.Name).startswith("Default__"))
    return list(islice(modes, MAX_MODES))


def _clock() -> Any:
    global _timer
    if _timer is None:
        _timer = new_timer()
    return _timer


def _line(step: str) -> str:
    request = STATE.request
    return f"leave {request.operation if request else '------'}: {step}"


def _say(step: str) -> None:
    report.note(_line(step))


def busy() -> bool:
    return STATE.phase != IDLE


def take_last(game: str) -> Result | None:
    """The end of the last request when it was for `game`, then forgotten: the page says it once, in the game or at
    the title screen, and an old end does not come back at every opening, after a later change included. Another
    game's end is left for that game's page."""
    ended = STATE.last
    if ended is None or ended.game != game:
        return None
    STATE.last = None
    return ended


def ask(game: str, current: str, wanted: str) -> bool:
    """Starts changing `game` from `current` to `wanted` by way of the main menu; False when it cannot start."""
    old, new = hunters.by_code(current), hunters.by_code(wanted)
    if (busy() or not isinstance(game, str) or ID_PATTERN.fullmatch(game) is None
            or old is None or new is None or old == new):
        return False
    if len(live_modes()) != 1:
        report.note("leave: not exactly one live game mode, nothing asked")
        return False
    try:
        _clock().start(_tick)
    except Exception as error:
        report.error_once("leave:clock", f"the clock of the return to the main menu did not start: {error!r}")
        return False
    try:
        ready.enable()
    except Exception as error:
        report.error_once("leave:hook", f"the title screen's hook did not start: {error!r}")
        _stop_clock()
        return False
    STATE.request = SimpleNamespace(operation=secrets.token_hex(3), game=game, current=current, wanted=wanted)
    STATE.phase, STATE.said_other = ASKED, False
    _say(f"asked, {old.name} to {new.name}")
    return True


def cancel() -> None:
    """Drops the request in progress, writing nothing: the mod was turned off."""
    if busy():
        _say("cancelled, nothing written")
        _finish(None)


def _stop_clock() -> None:
    try:
        _clock().stop()
    except Exception as error:
        report.error_once("leave:clock_stop", _line(f"the return's clock did not stop: {error!r}"))


def _stop_hook() -> None:
    try:
        ready.disable()
    except Exception as error:
        report.error_once("leave:hook_stop", _line(f"the title screen's hook did not stop: {error!r}"))


def _finish(outcome: switch.Outcome | None) -> None:
    request = STATE.request
    # Each released on its own, the clock first: a hook that does not stop must not keep the clock the next request
    # starts again.
    _stop_clock()
    _stop_hook()
    if request is not None and outcome is not None:
        # Only for an end of switch.change, taken after it returned: the file it just wrote. The stamp keeps a done
        # step ("click another game…") from being said again once the player followed it; leave's own ends changed
        # nothing and stay true, said once whatever the game writes since (coordinator's ruling, 2026-09-29).
        stamp = save_places.stamp(STATE.save) if STATE.phase == WRITING else None
        STATE.last = Result(request.game, request.current, request.wanted, outcome, stamp)
        _say(f"finished, {outcome.reason}")
    STATE.phase, STATE.request, STATE.save, STATE.stamp = IDLE, None, None, None


def _left_title() -> bool:
    """Whether the title screen is gone: no controller, which mods_base hands during a load, or one with a character.
    The title screen always has a controller."""
    pc = get_pc()
    return pc is None or getattr(pc, "OakCharacter", None) is not None


def _tick() -> None:
    try:
        _advance(now())
    except Exception as error:
        # Raised inside switch.change, the save or the trees may have changed: not a give-up that wrote nothing.
        reason = ERROR if STATE.phase == WRITING else GAVE_UP
        report.error_once("leave:tick", _line(f"the change asked in the game stopped after an error: {error!r}"))
        _finish(switch.Outcome(reason))


def _advance(at: float) -> None:
    if STATE.phase == ASKED:
        _return(at)
    elif STATE.phase in WAITING and at - STATE.called_at > AFTER_CALL_S:
        _say(f"gave up, no still save {AFTER_CALL_S:.0f} s after the call")
        _finish(switch.Outcome(GAVE_UP))
    elif STATE.phase in (SIGNALLED, SETTLING) and at - STATE.signal_at > AFTER_SIGNAL_S:
        _say(f"gave up, the save still moving {AFTER_SIGNAL_S:.0f} s after the title screen")
        _finish(switch.Outcome(GAVE_UP))
    elif STATE.phase == SIGNALLED:
        _find(at)
    elif STATE.phase == SETTLING:
        _settle(at)


def _return(at: float) -> None:
    modes = live_modes()
    if len(modes) != 1:
        _say(f"{len(modes)} live game modes, nothing called")
        _finish(switch.Outcome(NO_RETURN))
        return
    # Written before the call: a crash still says how far it went.
    _say("calling ReturnToMainMenuHost")
    STATE.phase, STATE.called_at = RETURNING, at
    try:
        modes[0].ReturnToMainMenuHost()
    except Exception as error:
        _say(f"ReturnToMainMenuHost refused: {type(error).__name__}")
        _finish(switch.Outcome(NO_RETURN))
        return
    _say("ReturnToMainMenuHost returned")


@hook(READY_PATH, Type.POST, hook_identifier=f"{__package__}:leave_ready")
def ready(_obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    try:
        _signal(now())
    except Exception as error:
        report.error_once("leave:ready", _line(f"the title screen's signal was skipped after an error: {error!r}"))


def _signal(at: float) -> None:
    if STATE.phase != RETURNING:
        return
    pc = get_pc()
    if pc is None or getattr(pc, "OakCharacter", None) is not None:
        return
    if game_id(getattr(pc, "PlayerState", None)) != STATE.request.game:
        if not STATE.said_other:
            STATE.said_other = True
            _say("title screen ready on another game, still waiting")
        return
    STATE.phase, STATE.signal_at = SIGNALLED, at
    _say("title screen ready")


def _find(at: float) -> None:
    save = save_places.find(STATE.request.game)
    if isinstance(save, save_places.Missing):
        _finish(switch.Outcome(save.why))
        return
    STATE.save, STATE.stamp, STATE.stable_since, STATE.phase = save, save_places.stamp(save), at, SETTLING


def _settle(at: float) -> None:
    # Another game selected meanwhile is no reason to stop: the message in the game asks the player to click another
    # game, and the change goes by the request's game id.
    if _left_title():
        _say("a game is loading or was loaded meanwhile, nothing written")
        _finish(switch.Outcome(LOADED))
        return
    stamp = save_places.stamp(STATE.save)
    if stamp is None or stamp != STATE.stamp:
        # Said once per new state: an unreadable save restarts the wait at every tick.
        if stamp != STATE.stamp:
            _say("the save cannot be read, waiting" if stamp is None else "the game wrote the save again, waiting")
        STATE.stamp, STATE.stable_since = stamp, at
        return
    if at - STATE.stable_since < SETTLE_S:
        return
    request = STATE.request
    STATE.phase = WRITING
    _say(f"the save is still {SETTLE_S:.0f} s, changing it")
    _finish(switch.change(request.game, request.current, request.wanted))
