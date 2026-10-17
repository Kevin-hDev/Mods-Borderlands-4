"""The duel, its one owner: started and stopped by the host in the window, beaten ten times a second by the frame hook
(heartbeat.py) while it goes on; its rounds are fight.py's. Two players only, the host and one guest (Kevin,
16 October 2026); no end, the host stops it (Kevin, 17 October 2026).

A duel always ends with each player back to normal: the one still KO stood up, the guest's own team given back.
It ends when the host stops it, when the mod is switched off, and on its own when the guest leaves, a third player
comes, the world changes (a travel: the characters are the game's new ones), the guest's team cannot be kept, or the
beat keeps failing.
"""

import time
from typing import NamedTuple

import mods_base

from . import players, report, teams, words
from .banner import Banner
from .fight import Fight
from .score import Score

STEP_S = 0.1
# What a refused start answers, each with its sentence in the window's texts (start_<refusal>).
REFUSALS = ("already_on", "not_host", "no_character", "in_vehicle", "no_guest", "too_many", "player_down",
            "team_refused")
# A give-back the game refused at the end of a duel is tried again this often, this many times: left in the duel's
# team, the guest would stay hostile to the host for the rest of the session.
RETURN_EVERY_S = 1.0
MAX_RETURNS = 10
MAX_FAILED_BEATS = 10


class View(NamedTuple):
    """What the window shows of a duel going on."""
    host_name: str
    guest_name: str
    host: int
    guest: int


_live: dict = {"duel": None}
# The guest whose own team is still to be given back, with the tries left and when the next one is due.
_return: dict = {"guest": None, "tries": 0, "at": 0.0}
_banner = Banner()
clock = time.monotonic


def _show(title: str, now: float, score: Score | None = None, sentence: str | None = None) -> None:
    try:
        _banner.show(mods_base.get_pc(), title, now, None if score is None else score.parts(), sentence)
    except Exception as error:
        report.note("message not shown", why=type(error).__name__)


def _round(fight: Fight, now: float) -> None:
    _show(words.text("banner_round", fight.language).format(round=fight.score.rounds), now, fight.score)


def refused(outcome: str, language: str) -> None:
    """A start the duel's key could not make, said on the screen with its cause and what to do, as the window's
    footer says it."""
    known = outcome in REFUSALS
    _show(words.text("banner_refused", language), clock(),
          sentence=words.text(f"start_{outcome}" if known else "start_refused", language))


def live() -> View | None:
    duel = _live["duel"]
    if duel is None:
        return None
    score = duel.score
    return View(score.host_name, score.guest_name, score.host, score.guest)


def start(language: str) -> str:
    """The duel started: "started", or why not, nothing changed then; a refusal is written with its cause."""
    outcome = _start(language)
    if outcome != "started":
        report.note("duel not started", why=outcome)
    return outcome


def _down(pawn) -> bool:
    """Whether the game shows the player down; unreadable reads as not down, the duel's beat asking again."""
    try:
        return pawn.InDownState() is True
    except Exception:
        return False


def _start(language: str) -> str:
    if _live["duel"] is not None:
        return "already_on"
    world = players.world()
    try:
        found = None if world is None else players.find(world)
    except Exception as error:
        report.note("players unreadable", error=type(error).__name__)
        return "no_character"
    if world is not None and found is None:
        return "not_host"
    if found is None or found.host is None:
        return "no_character"
    if not found.host_on_foot or found.riding:
        return "in_vehicle"
    if not found.guests:
        return "no_guest"
    if len(found.guests) > 1:
        return "too_many"
    # Down before the duel, by an enemy or a fall: scored at the first beat, it would count as the duel's round.
    if _down(found.host) or _down(found.guests[0]):
        return "player_down"
    number = report.begin_duel()
    guest = teams.take(found.guests[0])
    if guest is None or not guest.hand():
        if guest is not None:
            guest.give_back()
        return "team_refused"
    guest.hostile(found.host)
    score = Score(players.player_name(found.host, words.text("host", language)),
                  players.player_name(found.guests[0], words.text("guest", language)))
    now = clock()
    # His team is handed and read back: a give-back still pending from the last duel would undo it.
    _return["guest"] = None
    _live["duel"] = Fight(world, found.host, guest, score, language, now, _round)
    report.note("duel started", number=number, host=players.label(found.host), guest=guest.label)
    _show(words.text("banner_start", language), now, score)
    return "started"


def stop(why: str, show: bool = True) -> str:
    """The duel ended for why, every player back to normal: "stopped", or "not_running"."""
    duel = _live["duel"]
    if duel is None:
        return "not_running"
    _live["duel"] = None
    given = False
    try:
        given = duel.end(clock())
    finally:
        if not given:
            _return.update(guest=duel.guest, tries=MAX_RETURNS, at=clock() + RETURN_EVERY_S)
        report.note("duel over", why=why, host=duel.score.host, guest=duel.score.guest)
        if show:
            _show(words.text("banner_over", duel.language), clock(), duel.score)
        else:
            _banner.hide()
    return "stopped"


def hide() -> None:
    """The message taken off at once: the hook that would take it off goes with the mod."""
    _banner.hide()


def _give_back(now: float) -> None:
    """A refused give-back tried again, RETURN_EVERY_S apart, MAX_RETURNS times."""
    guest = _return["guest"]
    if guest is None or now < _return["at"]:
        return
    _return["tries"] -= 1
    _return["at"] = now + RETURN_EVERY_S
    if guest.pawn() is None:
        _return["guest"] = None
        return
    given = guest.give_back()
    if given or _return["tries"] <= 0:
        if not given:
            report.note("team never given back", character=guest.label)
        _return["guest"] = None


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
