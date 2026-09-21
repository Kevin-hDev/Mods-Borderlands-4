"""The mockup's slanted buttons: ink frame, flat fill, hard shadow and label, restyled by colour only.

Clicks are read from a latched CheckBox, so a short click cannot fall between two polls (control_view). Colours
change on the borders around it rather than on its own style, which Unreal does not redraw once built.
"""

from . import panel_text as tx, panel_theme as t, panel_widgets as w

TOGGLE_BUTTON = 1  # ESlateCheckBoxType::ToggleButton
# style: fill, frame, text, shadow; None is transparent. Each line is one class of the mockup's menu.css.
STYLES = {
    "primary": (t.COLOR_GOLD, t.COLOR_INK, t.COLOR_INK, t.COLOR_INK),
    "secondary": (t.COLOR_INK, t.COLOR_SPARK, t.COLOR_SPARK, t.COLOR_INK),
    "disabled": (t.COLOR_INK, t.COLOR_TEXT_DIM, t.COLOR_TEXT_DIM, None),
    "on": (t.COLOR_GOLD, t.COLOR_INK, t.COLOR_INK, t.COLOR_INK),
    "off": (t.COLOR_INK, t.COLOR_TEXT_DIM, t.COLOR_TEXT_DIM, None),
    "nav_on": (t.COLOR_GOLD, t.COLOR_INK, t.COLOR_INK, t.COLOR_INK),
    "nav_off": (None, None, t.COLOR_TEXT, None),
    "lang_on": (t.COLOR_GOLD, t.COLOR_INK, t.COLOR_INK, None),
    "lang_off": (t.COLOR_INK, t.COLOR_TEXT_DIM, t.COLOR_TEXT_DIM, None),
}
# kind: label kind, frame width, shadow offset, padding (CSS order), centred label, minimum width
KINDS = {
    "action": ("button", t.STROKE, t.SHADOW_MD, (t.SPACE_2, t.SPACE_6), True, None),
    "switch": ("button", t.STROKE, t.SHADOW_SM, (t.SPACE_2, t.SPACE_3), True, t.SWITCH_WIDTH),
    "master": ("button", t.STROKE, t.SHADOW_SM, (t.SPACE_2, t.SPACE_3), True, t.MASTER_WIDTH),
    "nav": ("nav", t.STROKE, t.SHADOW_MD, (t.SPACE_3, t.SPACE_4), False, None),
    "lang": ("small_button", t.STROKE_THIN, 0, (t.SPACE_1, t.SPACE_3), True, t.STATE_WIDTH),
}
_STATES = (("UncheckedImage", None), ("UncheckedHoveredImage", t.HOVER_OVERLAY),
           ("UncheckedPressedImage", t.PRESS_OVERLAY), ("CheckedImage", None),
           ("CheckedHoveredImage", t.HOVER_OVERLAY), ("CheckedPressedImage", t.PRESS_OVERLAY))


def _content(check, padding, centred, role):
    check.WidgetStyle.Padding = w.pad(tx.inset(padding[0], role), padding[1])
    if centred:
        check.HorizontalAlignment = w.enum("EHorizontalAlignment", "HAlign_Center")


def button(owner, widgets, name, kind, template, style):
    role, stroke, offset, padding, centred, minimum = KINDS[kind]
    frame, fill = w.framed(owner, None, stroke)
    check = w.new("CheckBox", fill)
    check.WidgetStyle.CheckBoxType = TOGGLE_BUTTON
    for field, veil in _STATES:
        tint, alpha = veil or (t.COLOR_INK, 0.0)
        w.style_brush(check.WidgetStyle, field, template, tint, alpha=alpha)
    label = tx.text(check, "", role, center=centred)
    w.cosmetic("button_content", lambda: _content(check, padding, centred, role))
    check.SetContent(label)
    check.SetIsChecked(False)
    fill.SetContent(check)
    body = frame
    if minimum is not None:
        body = w.new("SizeBox", owner)
        body.SetMinDesiredWidth(float(minimum))
        body.SetContent(frame)
    layers, shade = w.shadowed(owner, body, offset)
    w.slant(layers)
    widgets.update({name: check, f"{name}_label": label, f"{name}_fill": fill,
                    f"{name}_frame": frame, f"{name}_shadow": shade})
    paint(widgets, name, style)
    return layers


def paint(widgets, name, style):
    fill, frame, text, shadow = STYLES[style]
    for part, tint in (("fill", fill), ("frame", frame), ("shadow", shadow)):
        widgets[f"{name}_{part}"].SetBrushColor(w.linear(tint or t.COLOR_INK, 1.0 if tint else 0.0))
    widgets[f"{name}_label"].SetColorAndOpacity(w.slate(text))
