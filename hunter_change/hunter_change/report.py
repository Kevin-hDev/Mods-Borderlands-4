"""Bounded game-log messages for Hunter Change."""

from unrealsdk import logging

from .pack import NAME

MAX_ERRORS = 100
_errors: set[str] = set()


def reset() -> None:
    _errors.clear()


def note(message: str) -> None:
    logging.info(f"[{NAME}] {message}")


def error_once(key: str, message: str) -> None:
    if key in _errors or len(_errors) >= MAX_ERRORS:
        return
    _errors.add(key)
    logging.error(f"[{NAME}] {message}")
