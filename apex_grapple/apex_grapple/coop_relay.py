"""On a co-op host: who is told what of every player's grapple, so that each player sees the others' as each chose it
(Kevin, 17 October 2026: "les deux doivent voir les grappin/corde/crochet de l'autre", "chaque joueur conserve son
grappin").

The host hears of everything: its own ropes, and each guest's ropes and look (coop_link.py). It draws the guests'
(remote_ropes.py) and tells each guest of the host's and of the other guests' (coop_messages.py), never of the guest's
own, which its game already draws. The looks go round again every LOOK_EVERY_S, so that a guest who joins late, or
whose game started again, learns them without anyone changing a setting.
"""

from typing import Any

import mods_base

from . import coop_messages, game, look_code, remote_ropes

LOOK_EVERY_NS = 5_000_000_000
# Four players at most in Borderlands 4; the guests' looks come from other games, so the list is bounded all the same.
MAX_PLAYERS = 8

_looks: dict[int, int] = {}
_next_look_ns = 0


def player_id(controller: Any) -> int | None:
    state = getattr(controller, "PlayerState", None) if controller is not None else None
    return int(state.PlayerId) if state is not None else None


def _guests() -> list[tuple[Any, int]]:
    """Each guest's controller and PlayerId; none solo, or on a guest's game, where the others' controllers do not
    exist."""
    world = mods_base.ENGINE.GameViewport.World
    game_state = world.GameState if world else None
    if not game_state:
        return []
    found = []
    for state in list(game_state.PlayerArray)[:MAX_PLAYERS]:
        pawn = state.PawnPrivate
        controller = getattr(pawn, "Controller", None) if pawn else None
        if controller is not None and not pawn.IsLocallyControlled():
            found.append((controller, int(state.PlayerId)))
    return found


def _tell(text: str, skip: Any = None) -> None:
    for controller, _player in _guests():
        if controller != skip:
            coop_messages.send(controller, text)


def host_rope_start(anchor: tuple[float, float, float], flight_s: float) -> None:
    mine = player_id(game.controller())
    if mine is not None:
        _tell(coop_messages.start(mine, anchor, flight_s))


def host_rope_end() -> None:
    mine = player_id(game.controller())
    if mine is not None:
        _tell(coop_messages.release(mine))


def guest_rope_start(controller: Any, anchor: tuple[float, float, float], flight_s: float, now_ns: int) -> None:
    player = player_id(controller)
    if player is None:
        return
    remote_ropes.start(player, anchor, flight_s, now_ns)
    _tell(coop_messages.start(player, anchor, flight_s), skip=controller)


def guest_rope_end(controller: Any, now_ns: int) -> None:
    player = player_id(controller)
    if player is None:
        return
    remote_ropes.release(player, now_ns)
    _tell(coop_messages.release(player), skip=controller)


def guest_look(controller: Any, number: int) -> None:
    player = player_id(controller)
    if player is None or _looks.get(player) == number:
        return
    if player not in _looks and len(_looks) >= MAX_PLAYERS:
        return
    _looks[player] = number
    remote_ropes.look(player, number)
    _tell(coop_messages.look(player, number), skip=controller)


def tick(now_ns: int) -> None:
    """Every LOOK_EVERY_S on the host: each guest told every look but its own."""
    global _next_look_ns
    if now_ns < _next_look_ns:
        return
    _next_look_ns = now_ns + LOOK_EVERY_NS
    guests = _guests()
    present = {player for _controller, player in guests}
    for gone in [player for player in _looks if player not in present]:
        del _looks[gone]
    mine = player_id(game.controller())
    if mine is None:
        return
    own = look_code.mine()
    for controller, player in guests:
        coop_messages.send(controller, coop_messages.look(mine, own))
        for other, number in _looks.items():
            if other != player:
                coop_messages.send(controller, coop_messages.look(other, number))


def reset() -> None:
    global _next_look_ns
    _looks.clear()
    _next_look_ns = 0
