"""Which look each shot plays, and whether the grapple gun's can play at all: the one owner of that answer.

The grapple gun's look needs every piece of our container. One missing, or one refusing to move during a shot, and the
grapple takes the classic look until the game is started again: the two looks never mix, and the grapple always
works (docs/apex_grapple/pistolet-grappin/decisions.md, 2026-10-04). The six hunters have it (decisions.md, 14
October); a hunter we do not know, one added to the game later, keeps the classic look. The window says why on its
LOOK page, in a sentence that names the true cause and what to do (menu.NOTICES).
"""

from typing import Any

from . import look_hunter, look_settings, report, settings

OURS, CLASSIC = "ours", "classic"
# Why the grapple gun's look does not play, by the window's sentence for it (panel_en.TEXT): its pieces could not be
# loaded, one failed during a shot, or the hunter played is not one we know.
MISSING, FAILED, UNKNOWN_HUNTER = "look_missing", "look_failed", "look_unknown_hunter"

_stopped: str | None = None
_unknown_hunter = False


def for_shot(character: Any) -> str | None:
    """The look of `character`'s next shot: None while the rope is hidden."""
    global _unknown_hunter
    if not bool(settings.show_rope.value):
        return None
    if look_settings.look.value != look_settings.GRAPPLE_GUN or _stopped is not None:
        return CLASSIC
    _unknown_hunter = look_hunter.of(character) is None
    return CLASSIC if _unknown_hunter else OURS


def stop(why: str, cause: str) -> None:
    """The grapple gun's look gives way to the classic one for the rest of the game's run; `why` is MISSING or
    FAILED, `cause` what the log says."""
    global _stopped
    if _stopped is None:
        _stopped = why
    report.error_once(f"look:{why}", f"the grapple gun's look gave way to the classic one until the game restarts: "
                                     f"{cause}")


def notice() -> str | None:
    """The key of the LOOK page's sentence, or None while the grapple gun's look can play."""
    return _stopped or (UNKNOWN_HUNTER if _unknown_hunter else None)
