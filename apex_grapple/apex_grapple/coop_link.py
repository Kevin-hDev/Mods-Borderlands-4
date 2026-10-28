"""The one door between a co-op guest's grapple and the host: the game's own ServerSetBestGrappleable, both ways round.

On a guest, each rope is told to the host when it goes (its direction, coop_code.py) and when it lets go, and the
guest's look when it changes and every LOOK_EVERY_S, so that a host whose game started again learns it. Right after
each message the point the game itself last sent goes again: the host grapples the game's own way to the last point it
was told, and the guest's game tells it only when the aim changes. A message left alone made the next grapple of the
game fail once (verified in game, docs/coop/2026-10-17-grappin-invite.md, trial 2), so the game's sends are heard from
the moment the mod runs.

On the host, a message of ours from another player's game is kept from the game, which then never sees a target
change: a rope goes to coop_host.py, a look to coop_relay.py. The host's own ropes go to coop_relay.py, which tells the
guests.

Solo nothing is sent: the character is the authority, and there are no guests to tell.
"""

import time
from typing import Any

import unrealsdk
from mods_base import hook
from unrealsdk.hooks import Block, Type
from unrealsdk.unreal import WeakPointer

from . import coop_code, coop_host, coop_relay, game, look_code, report

SEND = "/Script/OakGame.OakPlayerController:ServerSetBestGrappleable"
LOOK_EVERY_NS = 5_000_000_000
HOST, GUESTS = "host", "guests"

_game_point: Any = None
_game_code = 0
_sending = False
# Who was told of the rope in progress: the host (on a guest), the guests (on the host), or nobody.
_told: str | None = None
_look_sent: int | None = None
_next_look_ns = 0


def reset() -> None:
    global _game_point, _game_code, _sending, _told, _look_sent, _next_look_ns
    _game_point, _game_code, _sending, _told, _look_sent, _next_look_ns = None, 0, False, None, None, 0


_authority: Any = None


def is_guest(character: Any) -> bool:
    global _authority
    if _authority is None:
        # The engine's own enum, the same for the whole game: looked up once rather than at every frame (review of
        # 2026-10-24).
        _authority = unrealsdk.find_enum("ENetRole").ROLE_Authority
    return character.GetLocalRole() != _authority


def tell_start(character: Any, anchor: tuple[float, float, float], flight_s: float) -> None:
    """A rope of the player's has gone. A failure costs the others' copy of it, never the rope."""
    global _told
    try:
        if is_guest(character):
            here = game.location(character)
            _send(coop_code.encode_rope(tuple(a - h for a, h in zip(anchor, here))))
            _told = HOST
        else:
            coop_relay.host_rope_start(anchor, flight_s)
            _told = GUESTS
    except Exception as exc:
        report.error_once("coop:tell", f"the other players could not be told of a rope: {exc!r}")


def tell_end() -> None:
    """The rope told has let go; nothing is sent for a rope that was never told."""
    global _told
    told, _told = _told, None
    if told is None:
        return
    try:
        if told == GUESTS:
            coop_relay.host_rope_end()
        else:
            _send(coop_code.RELEASE)
    except Exception as exc:
        report.error_once("coop:tell", f"the other players could not be told of a rope: {exc!r}")


def tick(character: Any, now_ns: int, guest: bool) -> None:
    """Every frame: a guest's look told to the host when it changes and every LOOK_EVERY_S. `guest` is is_guest's
    answer for this frame, asked once by the frame for every co-op step that needs it."""
    global _look_sent, _next_look_ns
    if not guest:
        return
    number = look_code.mine()
    if number == _look_sent and now_ns < _next_look_ns:
        return
    _look_sent, _next_look_ns = number, now_ns + LOOK_EVERY_NS
    _send(coop_code.encode_look(number))


def _send(code: int) -> None:
    global _sending
    pc = game.controller()
    if pc is None:
        return
    point = _game_point() if _game_point is not None else None
    _sending = True
    try:
        pc.ServerSetBestGrappleable(None, code)
        pc.ServerSetBestGrappleable(point, _game_code if point is not None else 0)
    finally:
        _sending = False


def heard(obj: Any, target: Any, code: int, now_ns: int) -> bool:
    """One ServerSetBestGrappleable going through this game. True keeps it from the game."""
    global _game_point, _game_code
    if obj == game.controller():
        if not _sending:
            # Held weakly: a point of a level left behind must not be kept, nor sent back.
            _game_point = WeakPointer(target) if target is not None else None
            _game_code = code
        return False
    if not coop_code.is_ours(target, code):
        return False
    if coop_code.kind(code) == coop_code.LOOK:
        coop_relay.guest_look(obj, coop_code.decode_look(code))
    else:
        coop_host.heard(obj, code, now_ns)
    return True


@hook(SEND, Type.PRE, hook_identifier=f"{__package__}:coop_link")
def on_send(obj: Any, args: Any, _ret: Any, _func: Any) -> Any:
    try:
        if heard(obj, args.GrappleableObject, int(args.GrappleTargetHash), time.perf_counter_ns()):
            return Block
    except Exception as exc:
        # Let through: a target the game should have had costs it one grapple at worst.
        report.error_once("coop:heard", f"a grapple target could not be read: {exc!r}")
    return None
