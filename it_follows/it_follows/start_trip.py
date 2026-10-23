"""The one owner of a trip to a starting point (docs/RUN/spec-points-de-depart.md, section 4): one trip at a time, its
hook set and taken off here only. session.py asks for a trip and is told how it ends; this module never touches the
window nor the run.

A trip goes from the open world only (World_P: the places are there), never while another is under way; a refusal
moves nothing. Then, each call to the game written before it is made: the player's place, the cover (start_cover.py,
the image black and the hunter shielded) from just before the teleport, the teleport onto Kevin's mark, which the game
answers True. At each image the player is put back on the mark, his speed set to nothing, until a floor lies at most
MARK_DROP_CM under it, the same for STABLE_S; then he is turned the way Kevin faced, and let go: the cover gives the
image back once the game gives the keys back, and the shield GRACE_S later. Once the cover is over, arrived() is
called: the horde starts as the player can play (decision 138: « il faudra faire en sorte que la horde s'active bien
quand l'écran noire ce sera dissiper »). Trials 96 and 97 verified this hold at the seven marks, the floor found after
2.1 to 6.4 s, and SetControlRotation taking bResetCamera (refused without it at trial 96).

No floor within HOLD_S, the trace broken, the cover given up before the player could play, or an error: the player
sent back where he left from and held there as on the mark, under the cover, until a floor stays under him (HOLD_S
at most): sent back once, he could land where the map had gone while he was away and fall through it (It Follows'
audit, 2026-10-19). Then the hook taken off, the cover given back, and failed(outcome). The character gone (a change
of map), or cancel(): all of it at once, the player put back once when he is still there. The
character and the controller are kept by weak pointers: a character kept without one was called after the game
deleted it, and the game crashed (BL4 Arena's trial T6). The holds are not written one by one, some 75 a second: the
log says the hold began, and how it ended with how many there were."""

import math
from typing import Any, Callable

import unrealsdk
from mods_base import hook
from unrealsdk.hooks import Type
from unrealsdk.unreal import WeakPointer

from . import ground, report, start_calls as calls, start_cover as cover, start_hold as hold
from .characters import game_thread

FRAME_HOOK = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
IDENTIFIER = "it_follows:start_trip"
WORLD = "World_P"
# Why a trip moved nothing, as session.py and the window name it.
NOT_OPEN_WORLD, TRIP_GOING, MOVE_FAILED = "not_open_world", "trip_going", "move_failed"
# How a trip ended badly.
NO_FLOOR, GONE, HOLD_FAILED, CANCELLED = "no_floor", "character_gone", "hold_failed", "cancelled"
FOUND = "found"

# The trips' count: each trip's lines carry its number.
_state: dict = {"number": 0}
# The trip under way: its number, place, weak pointers, where the player left from, its hook, its clocks and holds,
# the floor kept and since when, whether the player was let go, and session.py's two calls; where he is held (the
# mark, or home on his way back) and, on his way back, how the trip ended.
_trip: dict = {}
clock = hold.clock


def travelling() -> bool:
    return bool(_trip)


def _world(character: Any) -> str:
    try:
        return str(character.Outer.Outer.Name)
    except Exception as error:
        report.note("start_trip_world_unread", error=type(error).__name__)
        return ""


def refusal(character: Any) -> str:
    """Why a trip would move nothing now, "" when it may go."""
    if _world(character) != WORLD:
        return NOT_OPEN_WORLD
    return TRIP_GOING if travelling() else ""


def _vector(point: tuple) -> Any:
    return unrealsdk.make_struct("Vector", X=point[0], Y=point[1], Z=point[2])


def _shown(point: tuple) -> str:
    return " ".join(f"{value:.0f}" for value in point)


def _put(character: Any, point: tuple) -> None:
    character.K2_TeleportTo(DestLocation=_vector(point), DestRotation=character.K2_GetActorRotation())
    character.CharacterMovement.Velocity = _vector((0.0, 0.0, 0.0))


def go(place: Any, pc: Any, character: Any, arrived: Callable[[], None], failed: Callable[[str], None]) -> str:
    """Sends the player to place (start_places.Place): "" once he is on his way, else why nothing moved. arrived() once
    the cover is over, failed(outcome) when the trip ends badly; each called once, from the frame hook."""
    why = refusal(character)
    if why:
        report.note("start_trip_refused", place=place.number, why=why)
        return why
    _state["number"] += 1
    number = _state["number"]
    calls.say(number, f"to place {place.number}, {place.name}, mark {_shown(place.spot)}, facing {place.yaw:.0f}")
    done, here = calls.called(number, "the player's place", character.K2_GetActorLocation)
    if not done:
        return MOVE_FAILED
    home = (float(here.X), float(here.Y), float(here.Z))
    calls.say(number, f"from {_shown(home)}, {math.dist(home, place.spot) / 100:.0f} m away")
    cover.cover(number, character, pc)
    done, moved = calls.called(number, f"K2_TeleportTo {_shown(place.spot)}", lambda: character.K2_TeleportTo(
        DestLocation=_vector(place.spot), DestRotation=character.K2_GetActorRotation()))
    # The game answers whether it moved him: True at every trial. Anything else, he stayed where he was.
    if not done or moved is not True:
        if done:
            calls.say(number, f"the game refused the move, it answered {moved!r}"[:calls.ERROR_TEXT])
        cover.give_back("the move failed")
        return MOVE_FAILED
    now = clock()
    _trip.update(number=number, place=place, pawn=WeakPointer(character), pc=WeakPointer(pc), home=home, ticked=now,
                 arrived=arrived, failed=failed, trace=ground.GroundTrace(report.announce), back=None)
    _held(place.spot, now)
    # On the game's thread, as the hook: a call that comes elsewhere does nothing (game_thread.py).
    _trip["guard"] = game_thread.Guard(IDENTIFIER)
    _trip["hook"] = hook(FRAME_HOOK, Type.POST, hook_identifier=IDENTIFIER)(_frame)
    _trip["hook"].enable()
    calls.say(number, f"held on the mark until a floor stays under it {hold.STABLE_S:.0f} s, "
                      f"{hold.HOLD_S:.0f} s at most")
    return ""


def cancel(why: str) -> None:
    """The trip under way stopped as a failed one, outcome CANCELLED; nothing when none is."""
    if _trip:
        _end(f"cancelled: {why}", CANCELLED)


def _held(target: tuple, now: float) -> None:
    """The player held on target from now: no floor yet, not let go."""
    _trip.update(target=target, since=now, traced=now - hold.TRACE_EVERY_S, floor=None, steady=None, holds=0,
                 landed=False)


def _end(why: str, outcome: str | None) -> None:
    """The trip over, said. Ended well (outcome None): its hook off. Ended badly with the player still there: sent
    back and held there (_hold), the hook kept; once there, or when it cannot be (the character gone, cancel, a second
    end on the way back), the hook off, the player put back once if he was not yet, the cover given back, then
    failed() with the first outcome, or CANCELLED."""
    number, character = _trip["number"], _trip["pawn"]()
    calls.say(number, why)
    first = _trip["back"]
    if outcome is not None and first is None and outcome not in (GONE, CANCELLED) and character is not None:
        _trip["back"] = outcome
        _held(_trip["home"], clock())
        calls.say(number, f"sent back to {_shown(_trip['home'])}, held there until a floor stays under him "
                          f"{hold.STABLE_S:.0f} s, {hold.HOLD_S:.0f} s at most")
        return
    trip = dict(_trip)
    _trip.clear()
    trip["hook"].disable()
    if outcome is None:
        return
    if character is not None and first is None:
        calls.called(number, f"back where he left from, {_shown(trip['home'])}", lambda: _put(character, trip["home"]))
    cover.give_back("the trip ended badly")
    try:
        trip["failed"](CANCELLED if outcome == CANCELLED else first or outcome)
    except Exception as error:
        calls.say(number, f"telling the session failed ({type(error).__name__}: {str(error)[:calls.ERROR_TEXT]})")


def _steady(status: str, centre: tuple | None, now: float) -> bool:
    """Whether the same floor has been under the mark for STABLE_S; a floor that moves starts the wait again."""
    if status != FOUND or centre is None:
        _trip["floor"] = _trip["steady"] = None
        return False
    if _trip["floor"] is None or abs(centre[2] - _trip["floor"]) > hold.SAME_CM:
        _trip["floor"], _trip["steady"] = centre[2], now
        return False
    return now - _trip["steady"] >= hold.STABLE_S


def _face(number: int, yaw: float) -> None:
    """The player turned the way Kevin faced; said, not stopped on, when the game refuses (trial 96)."""
    pc = _trip["pc"]()
    if pc is None:
        calls.say(number, "not turned: the controller is gone")
        return
    calls.called(number, f"SetControlRotation, facing {yaw:.0f}", lambda: pc.SetControlRotation(
        unrealsdk.make_struct("Rotator", Pitch=0.0, Yaw=yaw, Roll=0.0), False))


def _hold(character: Any, now: float) -> None:
    """The player put back on the mark, or home on his way back, until a floor stays under it."""
    place, number, target, back = _trip["place"], _trip["number"], _trip["target"], _trip["back"]
    if now - _trip["since"] >= hold.HOLD_S:
        where = "where he left from" if back else "the mark"
        _end(f"no floor under {where} after {hold.HOLD_S:.0f} s and {_trip['holds']} holds", NO_FLOOR)
        return
    _put(character, target)
    _trip["holds"] += 1
    if now - _trip["traced"] < hold.TRACE_EVERY_S:
        return
    _trip["traced"] = now
    status, centre, _what = _trip["trace"].ground("start", character, target, hold.MARK_UP_CM, hold.MARK_DROP_CM)
    if status.startswith("call_failed"):
        _end(f"the floor could not be looked for ({status})", HOLD_FAILED)
        return
    if not _steady(status, centre, now):
        return
    if back:
        _end(f"back on a floor where he left from after {now - _trip['since']:.1f} s", back)
        return
    _face(number, place.yaw)
    _trip["landed"] = True
    cover.landed()
    calls.say(number, f"a floor under the mark for {hold.STABLE_S:.0f} s: let go on it after "
                      f"{now - _trip['since']:.1f} s and {_trip['holds']} holds")


def _arrive() -> None:
    arrived, number = _trip["arrived"], _trip["number"]
    _end("the cover is over: the player can play", None)
    try:
        arrived()
    except Exception as error:
        calls.say(number, f"starting the run failed ({type(error).__name__}: {str(error)[:calls.ERROR_TEXT]})")


def _frame(_obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    if not _trip or ("guard" in _trip and not _trip["guard"].here()):
        return
    now = clock()
    if now - _trip["ticked"] < hold.HOLD_EVERY_S:
        return
    _trip["ticked"] = now
    try:
        character = _trip["pawn"]()
        if character is None:
            _end("the character is gone, a change of map", GONE)
        elif not _trip["landed"]:
            _hold(character, now)
        elif cover.covered():
            pass
        elif cover.ended_well():
            _arrive()
        else:
            # The cover gave up (the keys never back, an error): the player may not be able to play, so no run (spec,
            # section 4.5; It Follows' audit, 2026-10-19).
            _end("the cover gave up before the player could play", HOLD_FAILED)
    except Exception as error:
        # Ended rather than raised out of the hook, which would repeat the error at every animation update.
        if _trip:
            _end(f"stopped on an error ({type(error).__name__}: {str(error)[:calls.ERROR_TEXT]})", HOLD_FAILED)
        else:
            report.note("start_trip_error_after_end", error=type(error).__name__, text=str(error)[:calls.ERROR_TEXT])
