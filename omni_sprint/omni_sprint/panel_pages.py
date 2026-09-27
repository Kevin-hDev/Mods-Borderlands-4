"""Page contents: one mockup card per settings group, and the key-capture card, each in a scrolling page."""

import unrealsdk

from . import panel_buttons as b, panel_slider as s, panel_text as tx, panel_theme as t, panel_widgets as w
from . import panel_key_view as keys

_SCROLL_THUMBS = (("NormalThumbImage", t.COLOR_GOLD), ("HoveredThumbImage", t.COLOR_GOLD_HI),
                  ("DraggedThumbImage", t.COLOR_GOLD_HI))
_SCROLL_TRACK = ("VerticalBackgroundImage", "VerticalTopSlotImage", "VerticalBottomSlotImage")
_SELECTOR_STATES = (("Normal", t.COLOR_INK), ("Hovered", t.COLOR_HOVER), ("Pressed", t.COLOR_HOVER),
                    ("Disabled", t.COLOR_INK))


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


def selector(owner, listening, template):
    widget = w.new("InputKeySelector", owner)
    widget.SetAllowGamepadKeys(True)
    widget.SetAllowModifierKeys(False)
    widget.SetEscapeKeys([unrealsdk.make_struct("Key", KeyName="Escape")])
    widget.SetKeySelectionText(listening)
    widget.SetCursor(w.enum("EMouseCursor", "Default"))
    w.cosmetic("selector", lambda: _selector_style(widget, template))
    return widget


def _selector_style(widget, template):
    for field, tint in _SELECTOR_STATES:
        w.style_brush(widget.WidgetStyle, field, template, tint)
    tx.configure(widget.TextStyle.Font, "button")
    widget.TextStyle.ColorAndOpacity = w.slate(t.COLOR_GOLD)
    widget.Margin = w.pad(t.SPACE_2, t.SPACE_6)


def controls_page(owner, widgets, template):
    page, body = scrolling_body(owner, template)
    rows = card(body, widgets, "controls")
    widgets["current"] = tx.text(rows, "", "gold", wrap=True)
    w.column(rows, widgets["current"], padding=w.pad(t.SPACE_2, 0))
    w.column(rows, keys.summary(rows, widgets), padding=w.pad(t.SPACE_1, 0))
    w.column(rows, keys.family_choice(rows, widgets, template), padding=w.pad(t.SPACE_3, 0))
    widgets["two_text"] = tx.text(rows, "", "label", wrap=True)
    _row(rows, widgets["two_text"], b.button(rows, widgets, "two", "switch", template, "off"))
    for name in ("first", "second"):
        w.column(rows, _selector_frame(rows, keys.selector(rows, widgets, name)),
                 padding=w.pad(t.SPACE_3, 0, 0), halign="Left")
    widgets["second"].SetIsEnabled(False)  # Only the two-key mode offers a second key.
    widgets["status"] = tx.text(rows, "", "status", wrap=True)
    w.column(rows, widgets["status"], padding=w.pad(t.SPACE_3, 0))
    w.column(rows, b.button(rows, widgets, "reset", "action", template, "secondary"), halign="Left")
    widgets["escape_hint"] = tx.text(rows, "", "hint", wrap=True)
    w.column(rows, widgets["escape_hint"], padding=w.pad(t.SPACE_3, 0))
    return page


def _selector_frame(owner, widget):
    frame = w.border(owner, t.COLOR_SPARK, t.STROKE)
    frame.SetContent(w.sized(owner, widget, width=t.SELECTOR_WIDTH))
    return w.slant(frame)
