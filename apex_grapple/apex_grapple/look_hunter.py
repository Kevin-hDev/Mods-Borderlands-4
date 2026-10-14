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


def of(character: Any) -> str | None:
    """The hunter's class as look_assets.HUNTERS names it, or None for one we do not know."""
    global _seen, _hunter
    if _seen is not None and _seen() is character:
        return _hunter
    try:
        definition = str(character.GbxActorData.GbxActorDef)
    except Exception as error:
        definition = ""
        report.error_once("look:hunter", f"the hunter could not be read, the grapple keeps its classic look: {error!r}")
    found = FIRST_NAME.match(definition)
    _seen = unreal.WeakPointer(character)
    _hunter = found.group(1) if found and found.group(1) in look_assets.HUNTERS else None
    report.note(f"hunter: {found.group(1) if found else 'unknown'}, "
                f"{'the grapple gun' if _hunter else 'the classic look only'}")
    return _hunter


def forget() -> None:
    global _seen, _hunter
    _seen, _hunter = None, None
