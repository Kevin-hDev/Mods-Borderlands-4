"""Runs the rope once per frame, on the player only, and keeps the keys bound to the player's own choices.

The key list is read again every second rather than once: Apex Movement found that at a vehicle
exit the gamepad's key was missing from it, and stayed unbound until the next level.

Anything that raises stops the pull and is written once. One broken frame must not repeat its error
at every animation update, and a rope left holding after an error would write the velocity forever.
"""

import time
from typing import Any

from mods_base import hook
from unrealsdk.hooks import Type

from . import control_window, game, game_grapple, grapple, input_list, keys, report, session, settings

KEYS_NS = 1_000_000_000

rope = grapple.Rope()
_next_keys_ns = 0


def _keep_keys(now_ns: int) -> None:
    global _next_keys_ns
    if now_ns < _next_keys_ns:
        return
    _next_keys_ns = now_ns + KEYS_NS
    mappings = game.input_mappings()
    if not mappings:
        return
    input_list.tell_once(mappings)
    if keys.is_bound() and keys.matches(mappings):
        return
    keys.unbind()
    if not keys.bind(mappings, rope):
        # An active rope cannot outlive the callbacks that release it.
        session.reset(rope)


def on_frame(obj: Any, now_ns: int) -> None:
    try:
        character = session.refresh(now_ns, rope)
        if character is None or obj != game.anim():
            return
        keys.observe(now_ns)
        _keep_keys(now_ns)
        if not rope.busy:
            game_grapple.aim_target(character, now_ns)
        for line in settings.keep_in_bounds():
            report.warning(line)
        rope.update(character, now_ns)
    except Exception:
        session.reset(rope)
        report.error_once("frame:pull", "the pull stopped after an error")


def stop() -> None:
    """Puts everything down at switch-off. Nothing to restore: the mod owns no game value."""
    global _next_keys_ns
    session.cleanup(control_window.cancel_for_gameplay, keys.unbind, lambda: session.reset(rope), input_list.reset, game.forget)
    _next_keys_ns = 0


# The identifier carries the package's own name, so this hook never replaces another mod's.
@hook("/Script/Engine.AnimInstance:BlueprintUpdateAnimation", Type.POST, hook_identifier=f"{__package__}:frame")
def tick(obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    on_frame(obj, time.perf_counter_ns())
