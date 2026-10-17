"""Which update notes open at the window's first opening after an update: those of the versions newer than the last
one whose notes the player saw and not newer than the one installed, the newest first, one page each
(panel_updates.py). Kevin, 2026-10-17: the pop-up It Follows has, in Apex Movement's full pack (« on va gérer apex
movement complet et c'est tout »: its separate files ship none of this) and in Apex Grapple.

The version seen is kept in the settings file. None kept, or one that is no version (the settings file written by
hand), reads as none seen: every note up to the one installed, once. These mods have no welcome to tell a new player
from one updating, so the settings file does: a player who had none when the mod loaded is new, and is given the
version installed as seen at once, the notes speaking of changes they never lived (Kevin, 2026-10-17); one updating
has a file and no version seen, and sees the notes.

Grapple's copy is the source; sync_menu_ui gives it to Apex Movement only.
"""

from typing import Any

from mods_base import HiddenOption

from . import release_notes

seen = HiddenOption("updates_seen", "")


def key(version: Any) -> tuple[int, ...] | None:
    """1.2.10 as (1, 2, 10), so that it comes after 1.2.9; None for what is no version."""
    if not isinstance(version, str):
        return None
    parts = version.split(".")
    if not all(part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def due(current: str, notes: tuple | None = None) -> list[tuple[str, dict]]:
    """The notes to open for the version installed, the newest first as release_notes.py keeps them; empty when none
    is due."""
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


def new_player(mod: Any, current: str) -> None:
    """A first install: the version installed counts as seen, saved at once so a second launch does not take the
    player for one updating."""
    seen.value = current
    mod.save_settings()
