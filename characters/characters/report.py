"""A mod's lines in the SDK log: one JSON line an event, each carrying the number of the run it belongs to, behind the
name of the mod that carries this copy (named: It Follows, Companions; a neutral name until then). Each mod's copy is
its own module, so two mods write under their own names.

The SDK log is the one trace a player has, and the one Kevin's trials read: named fields rather than sentences, so
that a line can be searched (spec, section 6). Each risky call to the game is written down before it is made, so that
the last line before a crash names it. The calls made every second for each enemy (teleports, walks, the zone that
follows) pass log=False and are not written: the log would grow by thousands of lines a minute.
"""

import json
import re
from typing import Any

from unrealsdk import logging

PREFIX = "[Characters]"
MAX_TEXT = 200
# A mod's name, as it shows in the mods list: short, letters, digits, spaces and & only.
MOD_NAME = re.compile(r"^[A-Za-z0-9 &]{1,40}$")
# A line longer than this is cut: a list read from the game must never fill the log.
MAX_LINE = 4000
# Fields every line carries itself: a field of the same name would replace them.
RESERVED = frozenset({"event", "run"})
# The window's errors (error_once), each written once: a handful in practice; past this, new kinds are dropped.
MAX_ERRORS = 100

_run = {"number": 0}
_errors: set[str] = set()


def named(mod: str) -> None:
    """The lines written from now on behind that mod's name, its own copy of this module's. A name that is not a
    mod's (MOD_NAME) raises ValueError: no line ever carries a text it was handed."""
    global PREFIX
    if not isinstance(mod, str) or not MOD_NAME.fullmatch(mod):
        raise ValueError("not a mod's name")
    PREFIX = f"[{mod}]"


def begin_run() -> int:
    """A new run's number, carried by every line until the next run begins."""
    _run["number"] += 1
    return _run["number"]


def note(event: str, **fields: Any) -> None:
    """One line: the event, the run, then the fields. A field named event or run raises TypeError."""
    clash = RESERVED & fields.keys()
    if clash:
        raise TypeError(f"a field is named {sorted(clash)[0]}")
    line = json.dumps({"event": event, "run": _run["number"], **fields}, ensure_ascii=True, separators=(",", ":"),
                      default=str)
    logging.info(f"{PREFIX} {line[:MAX_LINE]}")


def announce(call: str, log: bool = True, **fields: Any) -> None:
    """A call to the game, written before it is made; a call made at every sample passes log=False."""
    if log:
        note("call", call=call, **fields)


def said(text: str) -> None:
    """A sentence for the player who reads the log, such as why a run did not start."""
    logging.info(f"{PREFIX} {str(text)[:MAX_TEXT]}")


def error_once(key: str, message: str) -> None:
    """An error of the window (its generated modules call it, as in every window of ours), written once by key: the
    window polls many times a second, and an error written at each poll would flood the log."""
    if key in _errors or len(_errors) >= MAX_ERRORS:
        return
    _errors.add(key)
    logging.error(f"{PREFIX} {str(message)[:MAX_TEXT]}")
