"""Which hunter the player plays, for the grapple gun's look: each has its own holster (look_assets.HUNTERS).

Read in the character's own definition, GbxActorData.GbxActorDef, written FGbxDefPtr('Char_<class>', ...) in the
log (Vex's Char_DarkSiren in trial 1, docs/apex_grapple/pistolet-grappin/enquetes/2026-10-04-essais-en-jeu.md;
Loveless's Char_CorpoHacker on 2026-10-14). Only its first name counts: Loveless's definition names Char_DarkSiren
further in, and once taken her for Vex (decisions.md, 14 October). The answer is kept per character: a new level
brings a new character, read once. Unreadable, or a hunter we do not know, the grapple keeps its classic look, which
works for every hunter.
"""

import re
from typing import Any

from unrealsdk import unreal

from . import look_assets, report

FIRST_NAME = re.compile(r"FGbxDefPtr\('?Char_(\w+)")

_seen: Any = None
_hunter: str | None = None


def read(character: Any) -> tuple[str | None, str]:
    """(the hunter as look_assets.HUNTERS names it, or None for one we do not know; the name read, or 'unknown').
    Raises when the definition cannot be read."""
    found = FIRST_NAME.match(str(character.GbxActorData.GbxActorDef))
    name = found.group(1) if found else "unknown"
    return (name if name in look_assets.HUNTERS else None), name


def of(character: Any) -> str | None:
    """The player's hunter as look_assets.HUNTERS names it, or None for one we do not know."""
    global _seen, _hunter
    if _seen is not None and _seen() is character:
        return _hunter
    try:
        _hunter, name = read(character)
    except Exception as error:
        _hunter, name = None, "unknown"
        report.error_once("look:hunter", f"the hunter could not be read, the grapple keeps its classic look: {error!r}")
    _seen = unreal.WeakPointer(character)
    report.note(f"hunter: {name}, {'the grapple gun' if _hunter else 'the classic look only'}")
    return _hunter


def forget() -> None:
    global _seen, _hunter
    _seen, _hunter = None, None
