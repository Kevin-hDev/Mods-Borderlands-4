"""Page contents: one mockup card per settings group, each in a scrolling page."""

from . import panel_buttons as b, panel_slider as s, panel_text as tx, panel_theme as t, panel_widgets as w

_SCROLL_THUMBS = (("NormalThumbImage", t.COLOR_GOLD), ("HoveredThumbImage", t.COLOR_GOLD_HI),
                  ("DraggedThumbImage", t.COLOR_GOLD_HI))
_SCROLL_TRACK = ("VerticalBackgroundImage", "VerticalTopSlotImage", "VerticalBottomSlotImage")


def _scrollbar(scroll, template):
    style = scroll.WidgetBarStyle
    size = (t.SCROLLBAR_WIDTH, t.SCROLLBAR_WIDTH)
    for field, tint in _SCROLL_THUMBS:
        w.style_brush(style, field, template, tint, outline=t.STROKE, size=size)
    for field in _SCROLL_TRACK:
        w.style_brush(style, field, template, t.COLOR_SIDEBAR, size=size)
    scroll.SetScrollbarThickness(w.vector(t.SCROLLBAR_WIDTH, t.SCROLLBAR_WIDTH))
    scroll.SetScrollbarPadding(w.pad(0))


def scrolling_body(owner, template):
    """One scroll area whose padding leaves its scrollbar against the window edge."""
    scroll = w.new("ScrollBox", owner)
    body = w.new("VerticalBox", scroll)
    scroll.AddChild(body).SetPadding(w.pad(t.SPACE_7, t.SPACE_8, t.SPACE_9))
    w.cosmetic("scrollbar", lambda: _scrollbar(scroll, template))
    # Depending on the engine version the bar's width is read from its style or from the setter above: both are set.
    w.cosmetic("scrollbar_width", lambda: setattr(scroll.WidgetBarStyle, "Thickness", float(t.SCROLLBAR_WIDTH)))
    return scroll, body


def card(body, widgets, key):
    """Ink rim, hard shadow and orange title plate shared by every settings card."""
    frame, inner = w.framed(body, t.COLOR_CARD, t.STROKE, w.pad(t.SPACE_5, t.SPACE_6, t.SPACE_3))
    layers, _ = w.shadowed(body, frame, t.SHADOW_LG)
    w.column(body, layers, padding=w.pad(0, 0, t.SPACE_5))
    rows = w.new("VerticalBox", inner)
    inner.SetContent(rows)
    plate, fill = w.framed(rows, t.COLOR_SPARK, t.STROKE, w.pad(tx.inset(t.SPACE_1, "plate"), t.SPACE_4))
    widgets[f"heading:{key}"] = tx.text(fill, "", "plate")
    fill.SetContent(widgets[f"heading:{key}"])
    w.column(rows, w.slant(plate), padding=w.pad(0, 0, 0, t.SPACE_1), halign="Left")
    widgets[f"group:{key}"] = tx.text(rows, "", "desc", wrap=True)
    w.column(rows, widgets[f"group:{key}"], padding=w.pad(t.SPACE_3, 0, t.SPACE_1))
    return rows


def _row(rows, label, control, value=None):
    w.column(rows, w.line(rows, t.COLOR_HOVER, height=t.STROKE_THIN), padding=w.pad(t.SPACE_2, 0, 0))
    line = w.new("HorizontalBox", rows)
    w.row(line, w.sized(line, label, width=t.ROW_LABEL_WIDTH), valign="Center")
    w.row(line, control, padding=w.pad(0, t.SPACE_6), fill=value is not None, valign="Center")
    if value is not None:
        w.row(line, value, valign="Center")
    w.column(rows, line, padding=w.pad(t.SPACE_3, 0, 0))
    return line


def setting_rows(rows, options, widgets, template, expose_rows=False):
    """expose_rows registers each row as row:<name>, for a page that greys a whole row (mockup .row.muted)."""
    for option in options:
        name = option.identifier
        widgets[f"label:{name}"] = tx.text(rows, "", "label", wrap=True)
        if type(option.default_value) is bool:
            line = _row(rows, widgets[f"label:{name}"],
                        b.button(rows, widgets, f"setting:{name}", "switch", template, "off"))
        else:
            line = _row(rows, widgets[f"label:{name}"], s.slider(rows, widgets, option, template),
                        s.value_box(rows, widgets, name))
        if expose_rows:
            widgets[f"row:{name}"] = line
        widgets[f"description:{name}"] = tx.text(rows, "", "hint", wrap=True)
        w.column(rows, widgets[f"description:{name}"], padding=w.pad(t.SPACE_2, 0, t.SPACE_3))


def settings_page(owner, group, key, widgets, template):
    page, body = scrolling_body(owner, template)
    rows = card(body, widgets, key)
    setting_rows(rows, group.children, widgets, template)
    return page
