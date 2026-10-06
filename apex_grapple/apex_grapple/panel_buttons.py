"""The mockup's slanted buttons: ink frame, flat fill, hard shadow and label, restyled by colour only.

Clicks are read from a latched CheckBox, so a short click cannot fall between two polls (control_view). Colours
change on the borders around it rather than on its own style, which Unreal does not redraw once built.
"""

from . import panel_text as tx, panel_theme as t, panel_widgets as w

TOGGLE_BUTTON = 1  # ESlateCheckBoxType::ToggleButton
# style: fill, frame, text, shadow, as theme colour names read by colours(); None is transparent. Each line is one
# class of the mockup's menu.css. A transparent fill needs a transparent frame: the frame is a whole box under the
# fill, not a CSS border, and would show through in the label's colour.
STYLES = {
    "primary": ("COLOR_GOLD", "COLOR_INK", "COLOR_INK", "COLOR_INK"),
    "secondary": ("COLOR_INK", "COLOR_SPARK", "COLOR_SPARK", "COLOR_INK"),
    "disabled": ("COLOR_OFF", "COLOR_TEXT_DIM", "COLOR_TEXT_DIM", None),
    "on": ("COLOR_GOLD", "COLOR_INK", "COLOR_INK", "COLOR_INK"),
    "off": ("COLOR_OFF", "COLOR_TEXT_DIM", "COLOR_TEXT_DIM", None),
    "nav_on": ("COLOR_GOLD", "COLOR_INK", "COLOR_INK", "COLOR_INK"),
    "nav_off": (None, None, "COLOR_TEXT", None),
    "lang_on": ("COLOR_GOLD", "COLOR_INK", "COLOR_INK", None),
    "lang_off": ("COLOR_OFF", "COLOR_TEXT_DIM", "COLOR_TEXT_DIM", None),
}
# Movement's Options gear lives here too, because Grapple is the generated menus' visual authority.
# kind: label kind, frame width, shadow offset, padding (CSS order), centred label, minimum width
KINDS = {
    "action": ("button", t.STROKE, t.SHADOW_MD, (t.SPACE_2, t.SPACE_6), True, None),
    "switch": ("button", t.STROKE, t.SHADOW_SM, (t.SPACE_2, t.SPACE_3), True, t.SWITCH_WIDTH),
    "master": ("button", t.STROKE, t.SHADOW_SM, (t.SPACE_2, t.SPACE_3), True, t.MASTER_WIDTH),
    "nav": ("nav", t.STROKE, t.SHADOW_MD, (t.SPACE_3, t.SPACE_4), False, None),
    "lang": ("small_button", t.STROKE_THIN, 0, (t.SPACE_1, t.SPACE_3), True, t.STATE_WIDTH),
    # Apex Movement's Options tabs: a switch, wider for its word (sketch A of 2026-10-06, options_onglets).
    "tab": ("button", t.STROKE, t.SHADOW_SM, (t.SPACE_2, t.SPACE_5), True, None),
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


def gear(owner, widgets, template):
    """A gear made only from flat UMG shapes, matching mockup V2 without an image asset."""
    frame, fill = w.framed(owner, None, t.STROKE)
    check = w.new("CheckBox", fill)
    check.WidgetStyle.CheckBoxType = TOGGLE_BUTTON
    for field, veil in _STATES:
        tint, alpha = veil or (t.COLOR_INK, 0.0)
        w.style_brush(check.WidgetStyle, field, template, tint, alpha=alpha)
    icon = w.new("Overlay", check)
    for index, angle in enumerate((0, 45, 90, 135)):
        tooth = w.border(icon, t.COLOR_TEXT_DIM)
        tooth.SetRenderTransformAngle(float(angle))
        w.layer(icon, w.sized(icon, tooth, t.GEAR_TOOTH_WIDTH, t.GEAR_ICON_SIZE), halign="Center", valign="Center")
        widgets[f"options_icon:{index}"] = tooth
    ring = w.border(icon, t.COLOR_TEXT_DIM, (t.GEAR_RING_SIZE - t.GEAR_HUB_SIZE) / 2)
    hub = w.border(ring, t.COLOR_INK)
    ring.SetContent(hub)
    # Round ring and hole, as in the mockup; if the rounded brush is refused, the gear keeps square ones.
    w.cosmetic("gear_round", lambda: (w.round_shape(ring), w.round_shape(hub)))
    w.layer(icon, w.sized(icon, ring, t.GEAR_RING_SIZE, t.GEAR_RING_SIZE), halign="Center", valign="Center")
    widgets.update({"options_icon:4": ring, "options_icon:5": hub})
    check.SetContent(w.sized(check, icon, t.GEAR_ICON_SIZE, t.GEAR_ICON_SIZE))
    check.SetIsChecked(False)
    fill.SetContent(check)
    layers, shade = w.shadowed(owner, frame, t.SHADOW_MD)
    # Slanted, icon included, as every other button and its word (Kevin, 2026-10-06: the only square button).
    w.slant(layers)
    widgets.update({"options": check, "options_fill": fill, "options_frame": frame,
                    "options_shadow": shade})
    paint_gear(widgets, False)
    return w.sized(owner, layers, t.KEY_ICON_SIZE + t.SHADOW_MD, t.KEY_ICON_SIZE + t.SHADOW_MD)


def colours(style):
    """A style's fill, frame, text and shadow in the current theme."""
    return tuple(t.colour(name) for name in STYLES[style])


def paint(widgets, name, style):
    fill, frame, text, shadow = colours(style)
    for part, tint in (("fill", fill), ("frame", frame), ("shadow", shadow)):
        widgets[f"{name}_{part}"].SetBrushColor(w.linear(tint or t.COLOR_INK, 1.0 if tint else 0.0))
    widgets[f"{name}_label"].SetColorAndOpacity(w.slate(text))


def paint_gear(widgets, active):
    colour = t.COLOR_INK if active else t.COLOR_TEXT_DIM
    fill = t.COLOR_GOLD if active else t.COLOR_OFF
    widgets["options_fill"].SetBrushColor(w.linear(fill))
    widgets["options_frame"].SetBrushColor(w.linear(colour))
    widgets["options_shadow"].SetBrushColor(w.linear(t.COLOR_INK))
    for index in range(5):
        widgets[f"options_icon:{index}"].SetBrushColor(w.linear(colour))
    widgets["options_icon:5"].SetBrushColor(w.linear(fill))
