"""Which update notes open (decision 117, docs/RUN/spec-notes-de-mise-a-jour.md): those of the versions newer than
the last one whose notes the player saw and not newer than the one installed, the newest first, one page each
(panel_updates.py).

The version seen is kept in the settings file. None kept, or one that is no version (the settings file written by
hand), reads as none seen: every note up to the one installed, once. A player who never saw the welcome is new, and is
given the version installed as seen with it (panel_welcome.py): the notes speak of changes they never lived.
"""

from typing import Any

from mods_base import HiddenOption

from . import release_notes

seen = HiddenOption("updates_seen", "")


def key(version: Any) -> tuple[int, ...] | None:
    """1.0.10 as (1, 0, 10), so that it comes after 1.0.9; None for what is no version."""
    if not isinstance(version, str):
        return None
    parts = version.split(".")
    if not all(part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def due(current: str, notes: tuple | None = None) -> list[tuple[str, dict]]:
    """The notes to open for the version installed, current, the newest first as release_notes.py keeps them;
    empty when none is due."""
    top = key(current)
    if top is None:
        return []
    last = key(seen.value)
    found = []
    for version, texts in release_notes.NOTES if notes is None else notes:
        mine = key(version)
        if mine is not None and mine <= top and (last is None or mine > last):
            found.append((version, texts))
    return found
