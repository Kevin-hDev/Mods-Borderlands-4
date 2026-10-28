"""Writes the holster's lines in the SDK log, signed Tidy Weapons, its name before it joined Apex Heirloom on
2026-09-26: each weapon put away as it happens, each distinct failure once."""

from unrealsdk import logging

PREFIX = "[Tidy Weapons]"
# Bounded: a key per failure kind; past this, new kinds are dropped.
MAX_REPORTED = 50
# A line per weapon put away, bounded per switch-on: a long session must not fill the log, which the game only
# rewrites at its next launch.
MAX_NOTES = 2000

_reported: set[str] = set()
_notes = 0


def note(message: str) -> None:
    global _notes
    if _notes >= MAX_NOTES:
        return
    _notes += 1
    logging.misc(f"{PREFIX} {message}")


def error_once(key: str, message: str) -> None:
    # A key held down can fail at every frame: written each time, the failure would flood the log.
    if key in _reported or len(_reported) >= MAX_REPORTED:
        return
    _reported.add(key)
    logging.error(f"{PREFIX} {message}")


def reset() -> None:
    global _notes
    _reported.clear()
    _notes = 0
