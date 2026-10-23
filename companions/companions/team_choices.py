"""What the player chose on the window's VAULT HUNTERS and ALLIES pages: the team, by the characters' package's rules
(companions/roster.py: MOST names at most, the same one as often as wanted), and for each hunter his own outfit or
the player's colours, offered only on the card of the hunter the player plays (spec-compagnons.md, « Deux boutons de
tenue »). Companions' own (decision 69: each mod keeps its own choices), held in two hidden settings (settings.py)
written through the window's settings transaction.

Read tolerantly: an outfit that is none reads as his own. What changes a value gives a new one, never the setting's
own changed in place: the transaction compares the value before with the value after.
"""

from typing import Any

from . import settings
from .characters.companions import kinds, roster, tuning

MOST = roster.MOST
OUTFITS = tuning.OUTFITS


def names() -> list[str]:
    """The team's names, those known, MOST at most, in the order they were added."""
    return roster.names(settings.team.value)


def added(name: str) -> list[str] | None:
    """The team with one more of that name; None when it is full or the name unknown."""
    return roster.added(settings.team.value, name)


def removed(name: str) -> list[str]:
    """The team with one fewer of that name, the last one added."""
    return roster.removed(settings.team.value, name)


def outfit(name: str, value: Any = None) -> str:
    """That companion's outfit: the one kept for a hunter, his own otherwise."""
    held = settings.outfits.value if value is None else value
    kept = held.get(name) if isinstance(held, dict) else None
    return kept if isinstance(kept, str) and kept in OUTFITS else OUTFITS[0]


def with_outfit(name: str, chosen: str) -> dict:
    """Every hunter's outfit kept, that one's changed when it is a hunter and chosen an outfit; the others as read."""
    held = settings.outfits.value if isinstance(settings.outfits.value, dict) else {}
    hunters = [kind.name for kind in kinds.HUNTERS]
    kept = {known: outfit(known, held) for known in hunters if known in held}
    if name in hunters and chosen in OUTFITS:
        kept[name] = chosen
    return kept
