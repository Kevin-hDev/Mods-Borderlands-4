"""Every other player's grapple in co-op, as this game draws it: the one owner of what another player's grapple shows
here (Kevin, 17 October 2026: "les deux doivent voir les grappin/corde/crochet de l'autre", "chaque joueur conserve
son grappin").

Each player is named by the PlayerId its PlayerState carries in every game. What is known of each: its look
(look_code.py), and its rope going and letting go, told by the host (coop_messages.py) or, on the host, by the guest
itself (coop_relay.py). At each frame the player's character is looked up among the game's players, and its grapple
drawn on it: the grapple gun's (remote_look.py) for a hunter we know, the game's rope (remote_beam.py) otherwise or
with the classic look, nothing for a player who hides the rope. A look that changes is built again once no shot is in
progress; a character that changes (a level, a respawn) gets new pieces.

A failure costs that player's grapple alone, said once: the player's own grapple, and the others', go on.
"""

from typing import Any

import mods_base

from . import look_code, look_hunter, look_settings, remote_beam, remote_look, report

# Four players at most in Borderlands 4; the players named here come from other games, so the list is bounded anyway.
MAX_PLAYERS = 8
UNKNOWN_LOOK = look_code.COUNT


class _Remote:
    def __init__(self, player: int) -> None:
        self.player = player
        self.look_number = UNKNOWN_LOOK
        self.rebuild = False
        self.grapple: Any = None
        self.waiting: tuple | None = None
        self.broken = False


_remotes: dict[int, _Remote] = {}


def _remote(player: int) -> _Remote | None:
    found = _remotes.get(player)
    if found is None and len(_remotes) < MAX_PLAYERS:
        found = _remotes[player] = _Remote(player)
    return found


def look(player: int, number: int) -> None:
    remote = _remote(player)
    if remote is not None and remote.look_number != number:
        remote.look_number, remote.rebuild, remote.broken = number, True, False


def start(player: int, anchor: tuple, flight_s: float, now_ns: int) -> None:
    remote = _remote(player)
    if remote is None:
        return
    if remote.grapple is not None:
        _guarded(remote, lambda: remote.grapple.start(anchor, flight_s, now_ns))
    else:
        remote.waiting = (tuple(anchor), flight_s, now_ns)


def release(player: int, now_ns: int) -> None:
    remote = _remotes.get(player)
    if remote is None:
        return
    remote.waiting = None
    if remote.grapple is not None:
        _guarded(remote, lambda: remote.grapple.release(now_ns))


def _players() -> tuple[set[int], dict[int, Any]]:
    """Every player in the game, and each other player's character on foot, by PlayerId. A player in a vehicle, or
    between two lives, is still in the game: its look is kept for when it is back on foot."""
    world = mods_base.ENGINE.GameViewport.World
    game_state = world.GameState if world else None
    if not game_state:
        return set(), {}
    present, found = set(), {}
    for state in list(game_state.PlayerArray)[:MAX_PLAYERS]:
        present.add(int(state.PlayerId))
        pawn = state.PawnPrivate
        if pawn and not pawn.IsLocallyControlled() and getattr(pawn, "CharacterMovement", None) is not None:
            found[int(state.PlayerId)] = pawn
    return present, found


def make(character: Any, number: int) -> Any:
    """The grapple drawn for that look, None when that player hides the rope."""
    chosen = look_code.decode(number)
    if not chosen.shown:
        return None
    if chosen.look == look_settings.GRAPPLE_GUN:
        try:
            hunter, _name = look_hunter.read(character)
        except Exception:
            hunter = None
        if hunter is not None:
            return remote_look.GunGrapple(character, chosen, hunter)
    return remote_beam.BeamGrapple(character, chosen)


def _guarded(remote: _Remote, action) -> None:
    try:
        action()
    except Exception as exc:
        report.error_once(f"remote:{remote.player}", f"another player's grapple stopped being drawn: {exc!r}")
        remote.broken = True
        _drop(remote)


def _drop(remote: _Remote) -> None:
    grapple, remote.grapple = remote.grapple, None
    if grapple is not None:
        try:
            grapple.drop()
        except Exception as exc:
            report.error_once(f"remote:drop:{remote.player}", f"another player's grapple left pieces behind: {exc!r}")


def _follow(remote: _Remote, character: Any, now_ns: int) -> None:
    grapple = remote.grapple
    if grapple is not None and (grapple.character() != character or (remote.rebuild and not grapple.busy())):
        _drop(remote)
    if remote.grapple is None and not remote.broken:
        remote.grapple = make(character, remote.look_number)
        remote.rebuild = False
        if remote.grapple is not None and remote.waiting is not None:
            remote.grapple.start(*remote.waiting)
        remote.waiting = None
    if remote.grapple is not None:
        remote.grapple.tick(now_ns)


def tick(now_ns: int) -> None:
    present, players = _players()
    for remote in list(_remotes.values()):
        character = players.get(remote.player)
        if character is None:
            _drop(remote)
            if remote.player not in present and remote.waiting is None:
                del _remotes[remote.player]
            continue
        _guarded(remote, lambda: _follow(remote, character, now_ns))


def reset() -> None:
    """At switch-off: every other player's pieces removed."""
    for remote in list(_remotes.values()):
        _drop(remote)
    _remotes.clear()
    remote_beam.reset()
