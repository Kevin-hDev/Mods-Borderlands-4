"""Each new character of the player dressed for its game, once, from the frame hook our other mods already use; the
size of the look worn kept on it at each frame (stature.keep).

A game being loaded may have its character before its id or its pickers (wardrobe.WAIT): the character is tried again
after a pause, for a bounded time. A look refused is tried again a few times, then left until the next character; the
log says why, once. The frame hook runs for every animated body of the level, so a character already handled costs
one comparison.
"""

import time
import types
from typing import Any

from mods_base import get_pc, hook
from unrealsdk.hooks import Type
from unrealsdk.unreal import WeakPointer

from . import report, stature, wardrobe

HOOK_PATH = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
WAIT_S = 0.5
MAX_WAIT_S = 60.0
RETRY_S = 2.0
MAX_TRIES = 5

STATE = types.SimpleNamespace(current=None, done=False, tries=0, next_try=0.0, first_wait=None)


def reset() -> None:
    """The character in play is handled again at the next frame."""
    STATE.current = None


def _current() -> Any:
    return STATE.current() if STATE.current is not None else None


def on_frame(now: float) -> None:
    pc = get_pc(possibly_loading=True)
    character = getattr(pc, "OakCharacter", None) if pc is not None else None
    if character is None:
        return
    if _current() != character:
        STATE.current, STATE.done, STATE.tries, STATE.next_try, STATE.first_wait = (
            WeakPointer(character), False, 0, 0.0, None)
    stature.keep(character, now)
    if STATE.done or now < STATE.next_try:
        return
    result = wardrobe.settle(character, pc.PlayerState)
    if result == wardrobe.DONE:
        STATE.done = True
    elif result == wardrobe.WAIT:
        STATE.first_wait = now if STATE.first_wait is None else STATE.first_wait
        if now - STATE.first_wait >= MAX_WAIT_S:
            STATE.done = True
            report.error_once("wait", f"gave up waiting for the game to be ready after {MAX_WAIT_S:.0f} s; "
                                      "the look is set again on the next character")
        else:
            STATE.next_try = now + WAIT_S
    else:
        STATE.tries += 1
        if STATE.tries >= MAX_TRIES:
            STATE.done = True
            report.error_once("failed", f"the look could not be put on after {MAX_TRIES} tries, for the reasons "
                                        "above; tried again on the next character")
        else:
            STATE.next_try = now + RETRY_S


@hook(HOOK_PATH, Type.POST, hook_identifier=f"{__package__}:frame")
def tick(_obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    try:
        on_frame(time.perf_counter())
    except Exception as error:
        report.error_once("frame", f"the look was skipped after an error: {error!r}")
