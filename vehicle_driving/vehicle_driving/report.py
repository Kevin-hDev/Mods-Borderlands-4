"""Writes Vehicle Driving's lines in the SDK log: what changes as it happens, each distinct failure once."""

from unrealsdk import logging

PREFIX = "[Vehicle Driving]"
# Bounded: failure kinds are a handful in practice; past this, new kinds are dropped rather than stored.
MAX_REPORTED = 200
# What happens (a vehicle taken or left, a value the game rewrote) and the summaries written every 5 seconds a part
# works have a bound each, per switch-on: a long drive must not fill the log, which the game only rewrites at its next
# launch. Apart, because three summaries every 5 seconds spent a shared bound in about 55 minutes of driving, and
# nothing that happened after reached the log.
MAX_NOTES = 2000
MAX_SUMMARIES = 2000


class Summary(str):
    """A summary line, written every few seconds while a part works (the grip, the push, the camera)."""


_reported: set[str] = set()
_notes = 0
_summaries = 0


def note(message: str) -> None:
    global _notes, _summaries
    if isinstance(message, Summary):
        if _summaries >= MAX_SUMMARIES:
            return
        _summaries += 1
    else:
        if _notes >= MAX_NOTES:
            return
        _notes += 1
    logging.misc(f"{PREFIX} {message}")


def warning(message: str) -> None:
    logging.warning(f"{PREFIX} {message}")


def error_once(key: str, message: str) -> None:
    # Per-frame code: an error written every frame would flood the log, so each failure kind is written once.
    if key in _reported or len(_reported) >= MAX_REPORTED:
        return
    _reported.add(key)
    logging.error(f"{PREFIX} {message}")


def reset() -> None:
    global _notes, _summaries
    _reported.clear()
    _notes = _summaries = 0
