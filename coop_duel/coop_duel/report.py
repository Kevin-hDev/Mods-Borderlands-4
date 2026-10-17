"""Co-op Duel's lines in the SDK log: one JSON line an event, each carrying the number of the duel it belongs to.

The SDK log is the one trace a player has, and the one Kevin's trials read: named fields rather than sentences, so that
a line can be searched. Each call that changes the game is written down before it is made (called), so that the last
line before a crash names it. Players are named by their character's object name, never by their player name: the
score shows the player names on the screen only, and a log is shared far more widely than a screen.
"""

import json
from typing import Any, Callable

from unrealsdk import logging

PREFIX = "[Co-op Duel]"
MAX_TEXT = 200
# A line longer than this is cut: a list read from the game must never fill the log.
MAX_LINE = 4000
# Fields every line carries itself: a field of the same name would replace them.
RESERVED = frozenset({"event", "duel"})
# The window's errors (error_once), each written once: a handful in practice; past this, new kinds are dropped.
MAX_ERRORS = 100

_duel = {"number": 0}
_errors: set[str] = set()


def begin_duel() -> int:
    """A new duel's number, carried by every line until the next duel begins."""
    _duel["number"] += 1
    return _duel["number"]


def note(event: str, **fields: Any) -> None:
    """One line: the event, the duel, then the fields. A field named event or duel raises TypeError."""
    clash = RESERVED & fields.keys()
    if clash:
        raise TypeError(f"a field is named {sorted(clash)[0]}")
    line = json.dumps({"event": event, "duel": _duel["number"], **fields}, ensure_ascii=True,
                      separators=(",", ":"), default=str)
    logging.info(f"{PREFIX} {line[:MAX_LINE]}")


def shown(value: Any) -> str:
    """A value of the game as text, cut; never raises."""
    try:
        return str(value)[:MAX_TEXT]
    except Exception as error:
        return f"<unreadable {type(error).__name__}>"


def called(what: str, make: Callable[[], Any]) -> tuple[bool, Any]:
    """The call written, then made: (True, its answer), or (False, None) once its refusal is written."""
    note("call", what=what)
    try:
        return True, make()
    except Exception as error:
        note("refused", what=what, error=f"{type(error).__name__}: {shown(error)}")
        return False, None


def said(text: str) -> None:
    """A sentence for the player who reads the log."""
    logging.info(f"{PREFIX} {str(text)[:MAX_TEXT]}")


def error_once(key: str, message: str) -> None:
    """An error of the window (its generated modules call it, as in every window of ours), written once by key: the
    window polls many times a second, and an error written at each poll would flood the log."""
    if key in _errors or len(_errors) >= MAX_ERRORS:
        return
    _errors.add(key)
    logging.error(f"{PREFIX} {str(message)[:MAX_TEXT]}")


def reset() -> None:
    _errors.clear()
