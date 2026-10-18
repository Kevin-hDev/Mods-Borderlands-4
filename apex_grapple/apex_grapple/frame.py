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

from . import (control_window, coop_host, coop_link, coop_moves, coop_relay, game, game_grapple, grapple, input_list,
               key_hold, keys, remote_ropes, report, rope_effects, session, settings)

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
        key_hold.tick(rope, character, now_ns)
        rope.update(character, now_ns)
        rope_effects.tick(character, now_ns)
    except Exception:
        session.reset(rope)
        report.error_once("frame:pull", "the pull stopped after an error")
        return
    _others(character, now_ns)


def _others(character: Any, now_ns: int) -> None:
    """Co-op, apart: a failure there costs the other players' grapples, never the player's own rope."""
    try:
        coop_host.tick(now_ns)
    except Exception:
        coop_host.reset()
        report.error_once("frame:guests", "the co-op guests' ropes stopped after an error")
    try:
        coop_link.tick(character, now_ns)
        coop_relay.tick(now_ns)
    except Exception as exc:
        report.error_once("frame:coop", f"the other players could not be told of this grapple: {exc!r}")
    try:
        if coop_link.is_guest(character):
            coop_moves.step(character, rope.busy, now_ns)
    except Exception as exc:
        report.error_once("frame:moves", f"the moves sent to the host during a rope could not be set: {exc!r}")
    try:
        remote_ropes.tick(now_ns)
    except Exception as exc:
        report.error_once("frame:remote", f"the other players' grapples stopped being drawn: {exc!r}")


def stop() -> None:
    """Puts everything down at switch-off. The only game values the mod writes, a co-op host's trust in a guest
    (coop_trust.py) and a guest's move combining (coop_moves.py), are put back by coop_host.reset and
    coop_moves.reset."""
    global _next_keys_ns
    # coop_moves before game.forget: it puts the game's variable back through the character while it is still known.
    session.cleanup(control_window.cancel_for_gameplay, keys.unbind, lambda: session.reset(rope), input_list.reset,
                    coop_moves.reset, game.forget, coop_host.reset, coop_link.reset, coop_relay.reset, remote_ropes.reset)
    _next_keys_ns = 0


# The identifier carries the package's own name, so this hook never replaces another mod's.
@hook("/Script/Engine.AnimInstance:BlueprintUpdateAnimation", Type.POST, hook_identifier=f"{__package__}:frame")
def tick(obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    on_frame(obj, time.perf_counter_ns())
