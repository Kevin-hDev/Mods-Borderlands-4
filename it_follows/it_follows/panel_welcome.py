"""The welcome (decision 61; sketch 6 of esquisses_menu, validated by Kevin): over the whole window the first time it
opens, in two pages (decision 80). The first says that It Follows holds two modes, independent of each other, and
presents the Horde: what it does, its two inspirations, the film It Follows and Call of Duty: Black Ops Zombies, and
the caution about the PC (decisions 54 and 60); NEXT turns to the second, the normal mode: its four levels, and that
it is a first overhaul of the game's enemies, still evolving. LET'S GO closes it.

It is remembered as seen as soon as it shows (welcome.py), as BL4 Arena's: a game that crashes later must not show it
again."""

from typing import Any

from . import panel_buttons as b, panel_i18n as i18n, panel_overlay as overlay, panel_text as tx
from . import panel_theme as t, panel_warning as warning, panel_widgets as w, report, updates, welcome

KEY = "welcome"
# Its pages: each its sentence, then its two boxes, a title and words each.
PAGES = (("welcome_lead", (("welcome_film_title", "welcome_film"), ("welcome_zombies_title", "welcome_zombies"))),
         ("welcome_normal_lead", (("welcome_levels_title", "welcome_levels"),
                                  ("welcome_evolving_title", "welcome_evolving"))))
# The button under each page: NEXT, then LET'S GO.
BUTTONS = ("welcome_next", "welcome_go")


def _visible(widget: Any, shown: bool) -> None:
    widget.SetVisibility(w.enum("ESlateVisibility", "SelfHitTestInvisible" if shown else "Collapsed"))


def _box(owner: Any, widgets: dict, place: str) -> Any:
    frame, fill = w.framed(owner, t.COLOR_WINDOW, t.STROKE, w.pad(t.SPACE_4, t.SPACE_5))
    column = w.new("VerticalBox", fill)
    fill.SetContent(column)
    widgets[f"welcome_box_title:{place}"] = tx.text(column, "", "subtitle")
    w.column(column, widgets[f"welcome_box_title:{place}"])
    widgets[f"welcome_box_text:{place}"] = tx.text(column, "", "body", wrap=True)
    w.column(column, widgets[f"welcome_box_text:{place}"], padding=w.pad(t.SPACE_2, 0, 0))
    return frame


def _page(rows: Any, widgets: dict, index: int) -> Any:
    page = widgets[f"welcome_page:{index}"] = w.new("VerticalBox", rows)
    widgets[f"welcome_lead:{index}"] = tx.text(page, "", "lead", wrap=True)
    w.column(page, widgets[f"welcome_lead:{index}"], padding=w.pad(t.SPACE_4, 0, t.SPACE_5))
    boxes = w.new("HorizontalBox", page)
    for place in range(len(PAGES[index][1])):
        w.row(boxes, _box(boxes, widgets, f"{index}:{place}"), fill=True,
              padding=w.pad(0, 0, 0, t.SPACE_5 if place else 0))
    w.column(page, boxes)
    return page


def build(widgets: dict, template: Any) -> None:
    """The welcome, closed, over the whole window, on its first page."""
    rows = overlay.build(widgets, KEY, t.WELCOME_WIDTH)
    for index in range(len(PAGES)):
        page = _page(rows, widgets, index)
        if index == 0:
            w.column(page, warning.caution(page, widgets, "welcome_caution"), padding=w.pad(t.SPACE_5, 0, 0))
        w.column(rows, page)
    foot = w.new("HorizontalBox", rows)
    widgets["welcome_version"] = tx.text(foot, "", "meta")
    w.row(foot, widgets["welcome_version"], fill=True, valign="Center")
    for name in BUTTONS:
        widgets[f"{name}_box"] = b.button(foot, widgets, name, "action", template, "primary")
        w.row(foot, widgets[f"{name}_box"], valign="Center")
    w.column(rows, foot, padding=w.pad(t.SPACE_5, 0, 0))
    _turn(widgets, 0)


def _turn(widgets: dict, shown: int) -> None:
    """The welcome on page shown, its button under it."""
    for index in range(len(PAGES)):
        _visible(widgets[f"welcome_page:{index}"], index == shown)
        _visible(widgets[f"{BUTTONS[index]}_box"], index == shown)


def paint(widgets: dict, language: str) -> None:
    from . import __version__

    widgets[f"heading:{KEY}"].SetText(i18n.text("welcome_title", language))
    widgets[f"group:{KEY}"].SetText("")
    for index, (lead, boxes) in enumerate(PAGES):
        widgets[f"welcome_lead:{index}"].SetText(i18n.text(lead, language))
        for place, (title, text) in enumerate(boxes):
            widgets[f"welcome_box_title:{index}:{place}"].SetText(i18n.text(title, language))
            widgets[f"welcome_box_text:{index}:{place}"].SetText(i18n.text(text, language))
    widgets["welcome_caution"].SetText(i18n.text("caution", language))
    widgets["welcome_version"].SetText(f"{i18n.text('version', language)} {__version__}")
    for name in BUTTONS:
        widgets[f"{name}_label"].SetText(i18n.text(name, language))


def open_first(form: Any, widgets: dict) -> None:
    """The welcome shown on its first page, remembered as seen at once; to a new player, who never saw it, the version
    installed remembered with it as one whose notes were seen (updates.py)."""
    from . import __version__

    _turn(widgets, 0)
    overlay.show(form, widgets, KEY)
    new = welcome.new()
    changes = ((welcome.seen, welcome.EDITION), *(((updates.seen, __version__),) if new else ()))
    saved = form.model.save(changes)
    report.note("welcome_shown", edition=welcome.EDITION, new=new, saved=saved)


def poll(form: Any, widgets: dict) -> bool:
    """While the welcome shows, its buttons alone: NEXT turns to the normal mode's page, LET'S GO closes it. Whether it
    shows."""
    if form.popup != KEY:
        return False
    if form.take(widgets["welcome_next"]):
        _turn(widgets, 1)
        report.note("welcome_next")
    if form.take(widgets["welcome_go"]):
        from . import panel_popup
        panel_popup.hide(form, widgets)
        report.note("welcome_closed")
    return True
