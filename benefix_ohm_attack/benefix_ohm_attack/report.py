"""Writes the beam attack's lines in the SDK log: what it does as it happens, each failure once."""

from unrealsdk import logging

PREFIX = "[Benefix Ohm Attack]"
# Bounded: the keys are failure kinds, a handful in practice; past this, new kinds are dropped.
MAX_REPORTED = 100

_reported: set[str] = set()


def note(message: str) -> None:
    logging.info(f"{PREFIX} {message}")


def error_once(key: str, message: str) -> None:
    # Per-frame code: an error logged every frame would flood the log, so each failure kind is logged once.
    if key in _reported or len(_reported) >= MAX_REPORTED:
        return
    _reported.add(key)
    logging.error(f"{PREFIX} {message}")


def reset() -> None:
    _reported.clear()
