# Generated: BL4 Arena's arrival.py under It Follows' names; its comments speak of BL4 Arena's trips to
# its arenas. Never edited by hand: docs/RUN/outils/start_cover_copy.py writes this file.
"""The arrival hidden in black and the hunter shielded (spec, « Le voyage vers une arène »; Kevin's choice of 14
October, trial T16): the one owner of the image's fade and of the hunter's shield during a trip, its hook set and
taken off here only. The trip covers before its teleport, says when it lets the player go, and gives back when it ends
badly; this module never moves the player.

After a teleport to an arena the game holds the player's moving keys until 2 to 3 s after the place has loaded, in its
own code, out of reach of a mod (trials T11 to T14), and the world goes on meanwhile: a sniper aimed at Kevin as he
arrived (T14). So the image goes black at once and stays so (PlayerCameraManager:StartCameraFade, 0 to 1 in 0 s,
held), and the character cannot be damaged (Unreal's bCanBeDamaged, its value before kept). Once the trip has let the
player go and the game gives the keys back, the image comes back in FADE_IN_S; GRACE_S later the shield goes, back to
its value before, the player having seen where he stands. The keys alone are not enough: sent 500 m straight up, the
player had them 0.1 s after the teleport while the trip still held him in the air, and the image came back on the sky
(the mod's trial 13). Every other end gives both back at once: a trip that ends badly, the character or the controller
gone (a change of map), MAX_S without both, an error. One of the two the game refuses is said and left: the trip goes
on without it. The character and the controller are kept by weak pointers."""

from typing import Any

import unrealsdk
from unrealsdk.hooks import Type, add_hook, has_hook, remove_hook
from unrealsdk.unreal import WeakPointer

from . import start_calls as calls, start_hold as hold
from .characters import game_thread

FRAME_HOOK = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
IDENTIFIER = "it_follows:start_cover"
WHAT = "trip"
EVERY_S = 0.1
FADE_IN_S = 0.5
GRACE_S = 1.0
# The trip's longest hold, then the keys' longest wait with room (11.9 s seen, trial T11): past this, the trip or the
# game is not letting the player go.
MAX_S = hold.HOLD_S + 30.0

# The trip covered: its number, the character's and the controller's weak pointers, when the cover began and last
# looked, whether the trip let the player go, when the keys came back, the shield's value before (None: not set),
# whether the image is black.
_state: dict = {}
# Whether the last cover ended as it should, the keys back and GRACE_S gone, or had nothing to wait for.
_ended: dict = {"well": True}
# In seconds, as the trip's (start_hold.py): the tests move it.
clock = hold.clock


def covered() -> bool:
    return has_hook(FRAME_HOOK, Type.POST, IDENTIFIER)


def ended_well() -> bool:
    return _ended["well"]


def _fade(pc: Any, from_alpha: float, to_alpha: float, seconds: float, hold: bool) -> None:
    black = unrealsdk.make_struct("LinearColor", R=0.0, G=0.0, B=0.0, A=1.0)
    pc.PlayerCameraManager.StartCameraFade(FromAlpha=from_alpha, ToAlpha=to_alpha, Duration=seconds, Color=black,
                                           bShouldFadeAudio=False, bHoldWhenFinished=hold)


def _shield(character: Any, on: bool) -> None:
    character.bCanBeDamaged = not on


def cover(number: int, character: Any, pc: Any) -> None:
    """The image black and the hunter shielded, before the trip's teleport."""
    if _state:
        give_back("a new trip")
    _ended["well"] = True
    now = clock()
    try:
        kept = {"pawn": WeakPointer(character), "pc": WeakPointer(pc)}
    except Exception as error:
        # Nothing set yet: the trip goes on as it did before the cover, rather than stop on the cover's account.
        calls.say(number, f"no cover, the trip goes on without ({type(error).__name__}: "
                          f"{str(error)[:calls.ERROR_TEXT]})", WHAT)
        return
    _state.update(number=number, since=now, ticked=now, landed=False, free=None, was=None, black=False, **kept)
    done, was = calls.called(number, "the shield's state before", lambda: bool(character.bCanBeDamaged), WHAT)
    if done and calls.called(number, "the shield on, bCanBeDamaged False", lambda: _shield(character, True), WHAT)[0]:
        _state["was"] = was
    if calls.called(number, "StartCameraFade, black at once and held", lambda: _fade(pc, 0.0, 1.0, 0.0, True),
                    WHAT)[0]:
        _state["black"] = True
    if _state["was"] is None and not _state["black"]:
        _state.clear()
        calls.say(number, "neither black nor shielded: the trip goes on without", WHAT)
        return
    _ended["well"] = False
    # On the game's thread, as the hook: a call that comes elsewhere does nothing (game_thread.py).
    _state["guard"] = game_thread.Guard(IDENTIFIER)
    add_hook(FRAME_HOOK, Type.POST, IDENTIFIER, _frame)
    calls.say(number, f"black {_state['black']}, shielded {_state['was'] is not None}, until the trip lets go and the "
                      "keys come back", WHAT)


def landed() -> None:
    """The trip let the player go: from now on the keys end the cover. Nothing when nothing is covered."""
    if _state:
        _state["landed"] = True


def give_back(why: str) -> None:
    """The image and the shield back, whatever of them is still set, each on its own; nothing when nothing is."""
    if not _state:
        return
    number, pc, character = _state["number"], _state["pc"](), _state["pawn"]()
    if covered():
        remove_hook(FRAME_HOOK, Type.POST, IDENTIFIER)
    if _state["black"] and pc is not None:
        calls.called(number, "StopCameraFade, the image back at once", lambda: pc.PlayerCameraManager.StopCameraFade(),
                     WHAT)
    was = _state["was"]
    if was is not None and character is not None:
        calls.called(number, f"the shield off, bCanBeDamaged {was}", lambda: _shield(character, not was), WHAT)
    _state.clear()
    calls.say(number, f"cover over: {why}", WHAT)


def _look(now: float) -> None:
    character, pc = _state["pawn"](), _state["pc"]()
    if character is None or pc is None:
        give_back("the character or the controller is gone, a change of map")
        return
    number, held = _state["number"], now - _state["since"]
    if _state["free"] is None:
        if held >= MAX_S:
            give_back(f"the player still not free after {MAX_S:.0f} s")
            return
        if not _state["landed"] or pc.IsMoveInputIgnored():
            return
        _state["free"] = now
        calls.say(number, f"the game gave the keys back after {held:.1f} s", WHAT)
        if _state["black"] and calls.called(number, f"StartCameraFade, the image back in {FADE_IN_S} s",
                                            lambda: _fade(pc, 1.0, 0.0, FADE_IN_S, False), WHAT)[0]:
            _state["black"] = False
    if now - _state["free"] >= GRACE_S:
        _ended["well"] = True
        give_back(f"{GRACE_S:.0f} s after the keys")


def _frame(_obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    if not _state or ("guard" in _state and not _state["guard"].here()):
        return
    now = clock()
    if now - _state.get("ticked", 0.0) < EVERY_S:
        return
    _state["ticked"] = now
    try:
        _look(now)
    except Exception as error:
        # Given back rather than raised out of the hook, which would repeat the error at every animation update.
        give_back(f"stopped on an error ({type(error).__name__}: {str(error)[:calls.ERROR_TEXT]})")
