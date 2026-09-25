"""The gear page from mockup V2: camera choices and the menu language."""

from . import panel_buttons as b, panel_pages as p, panel_shortcut as sc
from . import panel_text as tx, panel_theme as t, panel_widgets as w


def _language_card(body, widgets, template):
    rows = p.card(body, widgets, "language")
    # The mockup's language card has no sentence under its plate: collapsed, the empty text takes no room.
    widgets["group:language"].SetVisibility(w.enum("ESlateVisibility", "Collapsed"))
    w.column(rows, w.line(rows, t.COLOR_HOVER, height=t.STROKE_THIN), padding=w.pad(t.SPACE_2, 0, 0))
    line = w.new("HorizontalBox", rows)
    widgets["menu_language"] = tx.text(line, "", "label", wrap=True)
    w.row(line, w.sized(line, widgets["menu_language"], width=t.ROW_LABEL_WIDTH), valign="Center")
    choices = w.new("HorizontalBox", line)
    for language, gap in (("EN", t.SPACE_3), ("FR", 0)):
        w.row(choices, b.button(choices, widgets, f"language:{language}", "switch", template, "off"),
              padding=w.pad(0, gap, 0, 0), valign="Center")
    w.row(line, choices, padding=w.pad(0, t.SPACE_6), valign="Center")
    w.column(rows, line, padding=w.pad(t.SPACE_3, 0, t.SPACE_3))


def _heading(body, widgets):
    """The mockup's page head: a tilted inked title, then a plain sentence (menu.css .mod-head)."""
    title = tx.text(body, "", "hero")
    title.SetRenderTransformPivot(w.vector(0.0, 0.5))
    title.SetRenderTransformAngle(float(t.TILT_TITLE))
    description = tx.text(body, "", "body", wrap=True)
    widgets["options_title"], widgets["options_description"] = title, description
    w.column(body, title)
    w.column(body, w.sized(body, description, width=t.DESC_MAX_WIDTH),
             padding=w.pad(t.SPACE_1, 0, t.SPACE_6), halign="Left")


def options_page(owner, model, widgets, template):
    page, body = p.scrolling_body(owner, template)
    _heading(body, widgets)
    if model.camera_options:
        sc.rows(p.card(body, widgets, "camera"), model.camera_options.values(), widgets, template)
    _language_card(body, widgets, template)
    return page
