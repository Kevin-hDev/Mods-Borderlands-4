"""Writes Apex Grapple's lines in the SDK log: what the grapple does as it happens, each failure once."""

from unrealsdk import logging

PREFIX = "[Apex Grapple]"
# Bounded: the keys are failure kinds, a handful in practice; past this, new kinds are dropped.
MAX_REPORTED = 200

_reported: set[str] = set()


def note(message: str) -> None:
    logging.misc(f"{PREFIX} {message}")


def warning(message: str) -> None:
    logging.warning(f"{PREFIX} {message}")


def error_once(key: str, message: str) -> None:
    # Per-frame code: an error logged every frame would flood the log, so each failure kind is logged once.
    if key in _reported or len(_reported) >= MAX_REPORTED:
        return
    _reported.add(key)
    logging.error(f"{PREFIX} {message}")


def reset() -> None:
    _reported.clear()
