"""What a co-op host tells each guest of the other players' grapples, in the engine's ClientMessage: a text the host
sends to one player's game, which arrives in a few hundredths of a second, never shows, and which the guest's mod
keeps from the game (verified in game, docs/coop/2026-10-17-grappin-invite.md, trial 3).

Three kinds, each about one player, named by the PlayerId its PlayerState carries in every game:
- "L <player> <look>": that player's look (look_code.py);
- "S <player> <x> <y> <z> <flight ms>": that player's rope goes, its hook there after the flight;
- "R <player>": that player's rope lets go.
Every text is read strictly: anything else, or out of its bounds, is dropped whole, said once.
"""

import math
import time
from typing import Any

from mods_base import hook
from unrealsdk.hooks import Block, Type

from . import game, look_code, remote_ropes, report

RECEIVE = "/Script/Engine.PlayerController:ClientMessage"
MARK = "ApexGrapple:1"
LOOK, START, RELEASE = "L", "S", "R"
MAX_TEXT = 120
MAX_PLAYER = 1 << 30
MAX_COORDINATE = 1e7
MAX_FLIGHT_MS = 10_000


def look(player: int, number: int) -> str:
    return f"{MARK} {LOOK} {player} {number}"


def start(player: int, anchor: tuple[float, float, float], flight_s: float) -> str:
    x, y, z = anchor
    return f"{MARK} {START} {player} {x:.1f} {y:.1f} {z:.1f} {int(round(flight_s * 1000))}"


def release(player: int) -> str:
    return f"{MARK} {RELEASE} {player}"


def _player(text: str) -> int:
    number = int(text)
    if not 0 <= number < MAX_PLAYER:
        raise ValueError("player out of range")
    return number


def _coordinate(text: str) -> float:
    value = float(text)
    if not math.isfinite(value) or abs(value) > MAX_COORDINATE:
        raise ValueError("coordinate out of range")
    return value


def parse(text: str) -> tuple | None:
    """(kind, player, ...) for a text of ours, None for any other text. Raises ValueError for one of ours that is
    malformed."""
    if not text.startswith(MARK + " "):
        return None
    if len(text) > MAX_TEXT:
        raise ValueError("text too long")
    parts = text.split(" ")[1:]
    kind = parts[0] if parts else ""
    if kind == LOOK and len(parts) == 3:
        number = int(parts[2])
        if not 0 <= number < look_code.COUNT:
            raise ValueError("look out of range")
        return LOOK, _player(parts[1]), number
    if kind == START and len(parts) == 6:
        flight_ms = int(parts[5])
        if not 0 <= flight_ms <= MAX_FLIGHT_MS:
            raise ValueError("flight out of range")
        anchor = (_coordinate(parts[2]), _coordinate(parts[3]), _coordinate(parts[4]))
        return START, _player(parts[1]), anchor, flight_ms / 1000.0
    if kind == RELEASE and len(parts) == 2:
        return RELEASE, _player(parts[1])
    raise ValueError(f"unknown kind {kind[:8]!r} with {len(parts)} parts")


def send(controller: Any, text: str) -> None:
    controller.ClientMessage(text, "None", 0.0)


def heard(obj: Any, text: str, now_ns: int) -> bool:
    """A ClientMessage going through this game. True keeps it from the game: one of ours, received by this game.

    On the host the same function runs as it sends to a guest's controller: those go through untouched."""
    if obj != game.controller() or not text.startswith(MARK):
        return False
    try:
        found = parse(text)
    except ValueError as exc:
        report.error_once("coop:message", f"a co-op message from the host was dropped: {exc}")
        return True
    if found is None:
        return True
    kind, player = found[0], found[1]
    try:
        if kind == LOOK:
            remote_ropes.look(player, found[2])
        elif kind == START:
            remote_ropes.start(player, found[2], found[3], now_ns)
        else:
            remote_ropes.release(player, now_ns)
    except Exception as exc:
        # Still ours: kept from the game whatever the drawing made of it.
        report.error_once("coop:message:draw", f"another player's grapple could not be drawn: {exc!r}")
    return True


@hook(RECEIVE, Type.PRE, hook_identifier=f"{__package__}:coop_messages")
def on_message(obj: Any, args: Any, _ret: Any, _func: Any) -> Any:
    try:
        if heard(obj, str(args.S), time.perf_counter_ns()):
            return Block
    except Exception as exc:
        report.error_once("coop:message:read", f"a co-op message could not be read: {exc!r}")
    return None
