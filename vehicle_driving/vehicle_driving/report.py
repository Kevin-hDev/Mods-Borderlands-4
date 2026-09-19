"""Writes Vehicle Driving's lines in the SDK log: what changes as it happens, each distinct failure once."""

from unrealsdk import logging

PREFIX = "[Vehicle Driving]"
# Bounded: failure kinds are a handful in practice; past this, new kinds are dropped rather than stored.
MAX_REPORTED = 200
# A line per vehicle taken, value the game rewrote and grip summary, bounded per switch-on: a long drive must not fill
# the log, which the game only rewrites at its next launch.
MAX_NOTES = 2000

_reported: set[str] = set()
_notes = 0


def note(message: str) -> None:
    global _notes
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
    global _notes
    _reported.clear()
    _notes = 0
