"""Writes Omni Sprint's lines in the SDK log: what changes as it happens, each distinct failure once."""

from unrealsdk import logging

PREFIX = "[Omni Sprint]"
# Bounded: a key per failure kind or per character's movement component; past this, new keys are dropped.
MAX_REPORTED = 200
# A line per definition opened or found back, bounded per switch-on: a long session must not fill the log, which the
# game only rewrites at its next launch.
MAX_NOTES = 2000

_reported: set[str] = set()
_notes = 0


def note(message: str) -> None:
    global _notes
    if _notes >= MAX_NOTES:
        return
    _notes += 1
    logging.misc(f"{PREFIX} {message}")


def warning_once(key: str, message: str) -> None:
    if _first(key):
        logging.warning(f"{PREFIX} {message}")


def error_once(key: str, message: str) -> None:
    # Code run twice a second: a failure written at each check would flood the log, so each kind is written once.
    if _first(key):
        logging.error(f"{PREFIX} {message}")


def _first(key: str) -> bool:
    if key in _reported or len(_reported) >= MAX_REPORTED:
        return False
    _reported.add(key)
    return True


def reset() -> None:
    global _notes
    _reported.clear()
    _notes = 0
