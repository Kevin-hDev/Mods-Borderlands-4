"""The duel, its one owner: started and stopped by the host in the window or by its key, beaten ten times a second by
the frame hook (heartbeat.py) while it goes on; its rounds are fight.py's. Two to four players, in the teams the host
arranged on the TEAMS page (roster.py; Kevin, 17 October 2026, docs/duel/spec-equipes.md); no end, the host stops it
(Kevin, 17 October 2026).

A duel always ends with each player back to normal: each one still down stood up, each one's own team given back. It
ends when the host stops it, when the mod is switched off, and on its own when a player comes, when fewer than two
teams are left, when the world changes (a travel: the characters are the game's new ones), when a team cannot be kept,
when a player is not stood up, or when the beat keeps failing.
"""

import sys
import time
from typing import Any, NamedTuple

import mods_base

from . import lineup, players, report, teams, words
from .banner import Banner
from .fight import Fight
from .fighters import Fighter
from .rounds import DRAW
from .score import Score

STEP_S = 0.1
# What a refused start answers (lineup.py), each with its sentence in the window's texts (start_<refusal>).
REFUSALS = ("already_on", "not_host", "no_character", "no_guest", "player_away", "in_vehicle", "one_team",
            "player_down", "team_refused")
# The ends said on the screen by a sentence, what to do next (stop_<why>), rather than by the score.
SAID = ("player_joined", "teams_left")
# A give-back the game refused at the end of a duel is tried again this often, this many times: left in the duel's
# team, a player would stay hostile to the others for the rest of the session.
RETURN_EVERY_S = 1.0
MAX_RETURNS = 10
MAX_FAILED_BEATS = 10


class View(NamedTuple):
    """What the window shows of a duel going on: the score's line."""
    line: str


_live: dict = {"duel": None}
# The players whose own team is still to be given back, with the tries left and when the next one is due.
_return: dict = {"members": [], "tries": 0, "at": 0.0}
_banner = Banner()
clock = time.monotonic


def _show(title: str, now: float, score: Score | None = None, sentence: str | None = None) -> None:
    try:
        _banner.show(mods_base.get_pc(), title, now, None if score is None else score.line(), sentence)
    except Exception as error:
        report.note("message not shown", why=type(error).__name__)


def _round(fight: Fight, now: float) -> None:
    """The round's number and its winner on the plate, the score under it."""
    language = fight.language
    if fight.outcome == DRAW:
        winner = words.text("banner_draw", language)
    else:
        winner = fight.score.alone(fight.outcome) or words.text("team_name", language).format(team=fight.outcome)
    _show(f"{words.text('banner_round', language).format(round=fight.score.rounds)} · {winner}", now, fight.score)


def refused(outcome: str, language: str) -> None:
    """A start the duel's key could not make, said on the screen with its cause and what to do, as the window's
    footer says it."""
    known = outcome in REFUSALS
    _show(words.text("banner_refused", language), clock(),
          sentence=words.text(f"start_{outcome}" if known else "start_refused", language))


def live() -> View | None:
    duel = _live["duel"]
    return None if duel is None else View(duel.score.text())


def start(language: str) -> str:
    """The duel started: "started", or why not, nothing changed then; a refusal is written with its cause."""
    outcome = _start(language)
    if outcome != "started":
        report.note("duel not started", why=outcome)
    return outcome


def _version() -> str:
    return str(getattr(sys.modules.get(__package__), "__version__", "unknown"))


def _start(language: str) -> str:
    if _live["duel"] is not None:
        return "already_on"
    world = players.world()
    read = lineup.read(world)
    return read if isinstance(read, str) else _begin(world, read, language)


def _retry(failed: list[Any]) -> None:
    """Give-backs the game refused, tried again by the beat (_give_back); one a player, the latest, so that refused
    starts in a row never pile them up."""
    if failed:
        kept = {member.number: member for member in [*_return["members"], *failed]}
        _return.update(members=list(kept.values()), tries=MAX_RETURNS, at=clock() + RETURN_EVERY_S)


def _give_back_now(fighters: list[Fighter]) -> None:
    """A start given up: each guest's own team given back, as at a duel's end, a refusal tried again."""
    _retry([fighter.member for fighter in fighters if fighter.member is not None and not fighter.member.give_back()])


def _begin(world: Any, read: lineup.Lineup, language: str) -> str:
    found, seats, sizes = read
    number = report.begin_duel()
    report.note("duel starting", version=_version(), players=len(found),
                teams=[sizes[team] for team in sorted(sizes)])
    given = teams.plan(sizes.keys(), seats[0].team)
    fighters: list[Fighter] = []
    for player, seat in zip(found, seats):
        member = None
        if not player.host:
            member = teams.take(player.pawn, seat.number, given[seat.team])
            if member is None:
                report.note("team not taken", player=report.player(seat.number))
                _give_back_now(fighters)
                return "team_refused"
        report.note("player", player=report.player(seat.number), character=players.label(player.pawn), team=seat.team,
                    given=given[seat.team], own="host, never changed" if member is None
                    else report.shown(member.own))
        fighters.append(Fighter(seat.number, seat.team, player.pawn, player.state, member))
    handed = [fighter.member.hand() for fighter in fighters if fighter.member is not None]
    if not all(handed):
        _give_back_now(fighters)
        return "team_refused"
    teams.attitudes([(fighter.number, fighter.pawn()) for fighter in fighters])
    score = Score({team: {} for team in sorted(sizes)})
    for seat in seats:
        fallback = words.text("player_fallback", language).format(number=seat.number)
        score.teams[seat.team][seat.number] = seat.name or fallback
    now = clock()
    # Their teams are handed and read back: a give-back still pending from the last duel would undo them.
    _return["members"] = []
    _live["duel"] = Fight(world, fighters, score, language, now, _round)
    report.note("duel started", number=number, players=len(fighters))
    _show(words.text("banner_start", language), now, score)
    return "started"


def stop(why: str, show: bool = True) -> str:
    """The duel ended for why, every player back to normal: "stopped", or "not_running"."""
    duel = _live["duel"]
    if duel is None:
        return "not_running"
    _live["duel"] = None
    # The cause first: a crash while standing a player up or giving his team back would leave it unsaid.
    report.note("duel ending", why=why)
    failed = duel.members()
    try:
        failed = duel.end(clock())
    finally:
        _retry(failed)
        report.note("duel over", why=why, rounds=duel.score.rounds, points=duel.score.points)
        title = words.text("banner_over", duel.language)
        if not show:
            _banner.hide()
        elif why in SAID:
            _show(title, clock(), sentence=words.text(f"stop_{why}", duel.language))
        else:
            _show(title, clock(), duel.score)
    return "stopped"


def hide() -> None:
    """The message taken off at once: the hook that would take it off goes with the mod."""
    _banner.hide()


def give_back_pending() -> None:
    """The mod switched off, the beat that tries refused give-backs again goes with it: each tried once more now, those
    still refused written down and tried again if the mod comes back on."""
    left = [member for member in _return["members"] if member.pawn() is not None and not member.give_back()]
    for member in left:
        report.note("team not given back, mod off", player=member.name)
    _return["members"] = left


def _give_back(now: float) -> None:
    """The refused give-backs tried again, RETURN_EVERY_S apart, MAX_RETURNS times."""
    pending = _return["members"]
    if not pending or now < _return["at"]:
        return
    _return["tries"] -= 1
    _return["at"] = now + RETURN_EVERY_S
    left = [member for member in pending if member.pawn() is not None and not member.give_back()]
    if left and _return["tries"] <= 0:
        for member in left:
            report.note("team never given back", player=member.name)
        left = []
    _return["members"] = left


def beat(now: float) -> None:
    """The frame hook's step: the message taken off once shown long enough, a refused give-back tried again, the
    duel beaten STEP_S apart."""
    _banner.tick(now)
    _give_back(now)
    duel = _live["duel"]
    if duel is None or now - duel.last < STEP_S:
        return
    duel.last = now
    try:
        why = duel.beat(now)
        duel.failed = 0
    except Exception as error:
        duel.failed += 1
        report.error_once(f"beat:{type(error).__name__}", f"a duel beat failed ({type(error).__name__})")
        why = "error" if duel.failed >= MAX_FAILED_BEATS else None
    if why is not None:
        stop(why)
