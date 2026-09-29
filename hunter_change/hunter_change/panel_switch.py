"""The HUNTER page (conception-idee-2.md, « La page CHASSEUR »): above the cards, in the APPEARANCE page's orange frame,
what a change keeps; the six hunter cards, YOUR HUNTER on the game's hunter; under them one sentence. In a game, a
click replaces the cards with the message and its two buttons, RETURN TO MAIN MENU and CANCEL. Where no change can be
made, no card: only the sentence saying why, or the end of the last change alone (panel_switch_text.py). The page's
state is switch_page.py's; this module only draws it and reads its clicks."""

from typing import Any

from . import hunters, menu, panel_buttons as b, panel_hunters as hunter_page, panel_i18n as i18n, panel_pages as p
from . import panel_switch_text as words, panel_text as tx, panel_theme as t, panel_widgets as w, switch_page as sp

KEY = menu.hunter.identifier.removesuffix("_menu")
PREFIX = "switch"
KEEPS = "keeps"
LEAVE = "leave"


def page(owner: Any, key: str, widgets: dict, template: Any, world: Any) -> Any:
    scroll, body = p.scrolling_body(owner, template)
    rows = p.card(body, widgets, key)
    widgets["switch_keeps"] = hunter_page.notice_block(rows, widgets, KEEPS)
    widgets["switch_grid"] = hunter_page.grid(rows, widgets, template, world, PREFIX)
    hunter_page.sentence(rows, widgets, "switch_state")
    confirm = w.new("VerticalBox", rows)
    widgets["switch_message"] = tx.text(confirm, "", "desc", wrap=True)
    w.column(confirm, widgets["switch_message"], padding=w.pad(0, 0, t.SPACE_5))
    line = w.new("HorizontalBox", confirm)
    w.row(line, b.button(line, widgets, "switch_leave", "action", template, "primary"),
          padding=w.pad(0, t.SPACE_5, 0, 0))
    w.row(line, b.button(line, widgets, "switch_cancel", "action", template, "secondary"))
    w.column(confirm, line, halign="Left")
    w.column(rows, confirm)
    widgets["switch_confirm"] = confirm
    return scroll


def paint(widgets: dict, view: sp.View, language: str) -> None:
    cards, asking = view.kind == sp.CARDS, view.kind == sp.CONFIRM
    hunter_page.show(widgets["switch_keeps"], cards)
    hunter_page.show(widgets["switch_grid"], cards)
    hunter_page.show(widgets["switch_state"], not asking)
    hunter_page.show(widgets["switch_confirm"], asking)
    hunter_page.paint_notice(widgets, KEEPS, language)
    widgets["switch_leave_label"].SetText(i18n.text("leave_button", language))
    widgets["switch_cancel_label"].SetText(i18n.text("cancel_button", language))
    for hunter in hunters.HUNTERS:
        own = hunter == view.current
        hunter_page.paint_card(widgets, PREFIX, hunter, language, own=own, chosen=False, framed=own)
    widgets["switch_state"].SetText(words.state(view, language))
    widgets["switch_message"].SetText(words.confirm(view, language))


def poll(form: Any, widgets: dict) -> str | bool:
    """The page's clicks, and the game followed while the window is open: LEAVE when the window must close for the
    return to the main menu, True after a click, False otherwise."""
    page_state = form.switch_page
    code = hunter_page.taken(form.take, widgets, PREFIX)
    if code is not None:
        page_state.click(code)
    elif form.take(widgets["switch_cancel"]):
        page_state.cancel()
    elif form.take(widgets["switch_leave"]):
        if page_state.leave():
            return LEAVE
    else:
        if page_state.follow():
            paint(widgets, page_state.view, form.model.language)
        return False
    paint(widgets, page_state.view, form.model.language)
    return True
