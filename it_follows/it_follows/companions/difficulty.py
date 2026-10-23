"""Reinforcements, trial 187: the level played, read from It Follows when a follow starts, in place of God written in.

A companion's health and shield go by It Follows' normal mode level (spec-compagnons.md, « L'équilibrage »; decisions
37 and 38): Bandit 4, Senior 7, Predator 9 and God 12 times the hunter's most health, the shield filled again at God
only. In the Horde and in the game alone no level of the normal mode is played: Bandit's (Kevin, 20 October 2026,
« toujours Bandit »).

It Follows' session.py is the one owner of what runs (its decision 80): normal_live() gives the normal mode on, with
its level, or None; running() whether a Horde run goes. The level is locked while the mode is on (normal/options.py,
LOCKED): read at the start, it holds for the follow. The session is found by the name the game loads it under, so that
this module needs no import of it: session.py owns the team, and an import of it here would go round in a circle.
Read only: nothing of It Follows is written or started.
"""

import sys
from typing import Any, NamedTuple

# By level: the hunter's most health times which, and the seconds a broken shield waits before it fills (None: never).
LEVELS = {"Bandit": (4.0, None), "Senior": (7.0, None), "Predator": (9.0, None), "God": (12.0, 45.0)}
OUTSIDE = "Bandit"
SESSION = "it_follows.session"
MAX_TEXT = 40


class Played(NamedTuple):
    """A level, why it was chosen, and what it gives: health times the hunter's, a broken shield's wait (None:
    never)."""
    name: str
    why: str
    times: float
    refill_after_s: float | None


def level(name: str, why: str) -> Played:
    """The level of that name (one of LEVELS), with why it was chosen."""
    times, refill_after_s = LEVELS[name]
    return Played(name, why, times, refill_after_s)


def played(session: Any = None) -> Played:
    """The level a companion starting now takes. "normal": the normal mode's, on. Bandit's otherwise, why said:
    "horde", a run going; "off", neither; "no_it_follows", It Follows not loaded; "unknown:<name>", a level this table
    lacks; "unread:<error>", a read that failed. session: It Follows' session module, the one the game loaded if
    none."""
    if session is None:
        session = sys.modules.get(SESSION)
    if session is None:
        return level(OUTSIDE, "no_it_follows")
    try:
        live = session.normal_live()
        if live is None:
            return level(OUTSIDE, "horde" if session.running() is True else "off")
        name = str(live.level)
    except Exception as error:
        return level(OUTSIDE, f"unread:{type(error).__name__}")
    if name not in LEVELS:
        return level(OUTSIDE, f"unknown:{name[:MAX_TEXT]}")
    return level(name, "normal")
