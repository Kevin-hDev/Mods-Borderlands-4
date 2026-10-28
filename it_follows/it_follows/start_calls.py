"""Each call of a trip to a starting point to the game, written in the log before it is made, with the trip's number:
the log outlives a crash, and its last line then names the call. A call that raises is written with its error and
answers (False, None). The cover (start_cover.py, BL4 Arena's copied) speaks through here as BL4 Arena's does through
its own calls.py, its `what` always a trip."""

from typing import Any, Callable

from . import report

# Of an error's own words, as much as a line of the log keeps.
ERROR_TEXT = 200


def say(number: int, text: str, _what: str = "trip") -> None:
    report.note("start_trip", trip=number, step=str(text)[:report.MAX_LINE])


def called(number: int, label: str, make: Callable[[], Any], _what: str = "trip") -> tuple[bool, Any]:
    say(number, f"call {label}")
    try:
        return True, make()
    except Exception as error:
        say(number, f"{label} failed ({type(error).__name__}: {str(error)[:ERROR_TEXT]})")
        return False, None
