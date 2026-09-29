"""Keeps the heirloom in the player's hands while it runs, the mod on and its switch on (parts.py): the knife goes on
the character's hands at their first frame, and again on a new character's, after a death or a new map (a fast
travel within the world kept the same character on 2026-09-26); switched off, it leaves at the next weapon change,
and switched on again before, it stays.

Why, 2026-09-26 (cosmetics/heirloom/docs/heirloom.md, section 17): until the menu, Kevin put the knife in the hand by
typing a console command at each session. A mod does it alone, and has to find the player's arms again whenever the
game builds new ones: what happens to our knife then is not known yet, so the new hands are watched rather than
guessed. The frame of the arms' animation says whose arms they are for nothing; finding the arms costs a search over
every animation instance, done only when the knife is not on them.
"""

import time
import types
from typing import Any

from mods_base import get_pc, hook
from unrealsdk.hooks import Type
from unrealsdk.unreal import WeakPointer

from . import heirloom
from .apex_holster_follow import FRAME_HOOK

# A knife that could not be put in the hand (our container missing, the game's picker not loaded yet) is tried again
# this often, and given up after so many tries for the same character, said: the log then holds why, once.
RETRY_S = 2.0
MAX_TRIES = 5

# Whether the heirloom runs; the character tried last, how many tries it had, and when the next may come.
STATE = types.SimpleNamespace(running=False, tried=None, tries=0, next_try=0.0)


def turn_on() -> None:
    STATE.running, STATE.tried, STATE.tries, STATE.next_try = True, None, 0, 0.0
    heirloom.switch_on()


def turn_off() -> None:
    STATE.running = False
    heirloom.switch_off()


def _tried() -> Any:
    return STATE.tried() if STATE.tried is not None else None


def keep(owner: Any, now: float) -> None:
    """The knife on `owner`'s hands, unless it is there already, they are not the player's, or tries wait."""
    if heirloom.holds_for(owner):
        return
    pc = get_pc()
    if pc is None or getattr(pc, "OakCharacter", None) != owner:
        return
    if _tried() != owner:
        STATE.tried, STATE.tries, STATE.next_try = WeakPointer(owner), 0, 0.0
    if now < STATE.next_try:
        return
    try:
        shown = heirloom.show(owner)
    except Exception as exc:
        heirloom.say(f"the knife could not be put in the hand: {exc!r}")
        shown = False
    if shown:
        STATE.tries = 0
        return
    STATE.tries += 1
    if STATE.tries < MAX_TRIES:
        STATE.next_try = now + RETRY_S
        return
    STATE.next_try = float("inf")
    heirloom.say(f"no knife after {MAX_TRIES} tries, the reasons above: tried again on a new character or when the mod "
                 "is switched on")


@hook(FRAME_HOOK, Type.POST)
def arms_frame(obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    if not STATE.running:
        return
    owner = getattr(obj, "OakCharacter", None)
    if owner is not None:
        keep(owner, time.perf_counter())
