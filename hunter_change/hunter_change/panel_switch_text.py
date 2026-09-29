"""The HUNTER page's sentences, from its view (switch_page.View): what the page says where it is, and the message of
a change asked in a game (conception-idee-2.md, « En partie »)."""

from . import leave, panel_i18n as i18n, save_places, switch, switch_page as sp

# Each end of a change, said in a few words and what to do next: several reasons read the same to a player.
SAID = {
    switch.DONE: "said:done",
    save_places.NO_SAVE: "said:no_save",
    save_places.TWO_SAVES: "said:two_saves",
    save_places.SAVES_UNSURE: "said:saves_unsure",
    save_places.SAVE_DAMAGED: "said:save_damaged",
    "not_this_hunter": "said:changed",
    "unknown_hunter": "said:unsafe", "foreign_tree": "said:unsafe", "prepare_failed": "said:unsafe",
    "trees_unreadable": "said:trees",
    "backup_failed": "said:not_written", "trees_failed": "said:not_written", "write_failed": "said:not_written",
    "restored": "said:not_written",
    "unverified": "said:unverified",
    "restore_failed": "said:restore_failed",
    leave.NO_RETURN: "said:no_return",
    leave.GAVE_UP: "said:gave_up",
    leave.LOADED: "said:loaded",
    leave.ERROR: "said:error",
}


def _said(view: sp.View, language: str) -> str:
    """The end of the last change: its sentence names the hunter asked for."""
    new = view.said_to.name if view.said_to is not None else view.current.name if view.current else ""
    return i18n.text(SAID.get(view.said.reason, "said:error"), language).format(new=new)


def state(view: sp.View, language: str) -> str:
    # An end is said alone: it carries its own next step, which a second sentence could contradict (restore_failed
    # beside why:no_save once told the player both not to load the game and to load it).
    if view.said is not None:
        return _said(view, language)
    if view.kind == sp.NOWHERE:
        return i18n.text("switch_nowhere", language)
    if view.kind == sp.BUSY:
        return i18n.text("switch_busy", language)
    if view.kind == sp.UNAVAILABLE:
        return i18n.text(f"why:{view.why}", language)
    if view.kind != sp.CARDS:
        return ""
    key = "switch_in_game" if view.in_game else "switch_at_title"
    return i18n.text(key, language).format(current=view.current.name)


def confirm(view: sp.View, language: str) -> str:
    if view.kind != sp.CONFIRM:
        return ""
    new, old = view.wanted.name, view.current.name
    tree = i18n.text("tree_back" if view.kept else "tree_first", language).format(new=new)
    return i18n.text("confirm", language).format(new=new, old=old, tree=tree)
