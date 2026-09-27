"""Controller icon layout, using the existing menu's buttons, spacing and colours."""

from . import panel_buttons as b, panel_text as tx, panel_theme as t, panel_widgets as w


def icon(owner, widgets, name):
    image = w.new("Image", owner)
    image.SetVisibility(w.enum("ESlateVisibility", "Collapsed"))
    widgets[name] = image
    box = w.sized(owner, image, t.KEY_ICON_SIZE, t.KEY_ICON_SIZE)
    box.SetVisibility(w.enum("ESlateVisibility", "HitTestInvisible"))
    return box


def selector(owner, widgets, name):
    overlay = w.new("Overlay", owner)
    native = widgets[name]
    w.layer(overlay, native)
    w.layer(overlay, icon(overlay, widgets, f"{name}:icon"), halign="Center", valign="Center")
    label = tx.text(overlay, "", "gold", center=True)
    label.SetVisibility(w.enum("ESlateVisibility", "Collapsed"))
    widgets[f"{name}:key_label"] = label
    w.layer(overlay, label, halign="Center", valign="Center")
    box = w.sized(owner, overlay, width=t.SELECTOR_WIDTH)
    box.SetMinDesiredHeight(float(t.KEY_ICON_SIZE + t.SPACE_2))
    return box


def summary(owner, widgets):
    row = w.new("HorizontalBox", owner)
    widgets["pad_summary"] = row
    row.SetVisibility(w.enum("ESlateVisibility", "Collapsed"))
    widgets["pad_label"] = tx.text(row, "", "gold")
    w.row(row, widgets["pad_label"], padding=w.pad(0, t.SPACE_2), valign="Center")
    w.row(row, icon(row, widgets, "pad_first"), valign="Center")
    widgets["pad_separator"] = tx.text(row, "+", "gold")
    w.row(row, widgets["pad_separator"], padding=w.pad(0, t.SPACE_2), valign="Center")
    box = icon(row, widgets, "pad_second")
    widgets["pad_second_box"] = box
    w.row(row, box, valign="Center")
    return row


def family_choice(owner, widgets, template):
    row = w.new("HorizontalBox", owner)
    widgets["icons_label"] = tx.text(row, "", "label")
    w.row(row, widgets["icons_label"], padding=w.pad(0, t.SPACE_3), valign="Center")
    for family in ("PS5", "XSX"):
        w.row(row, b.button(row, widgets, f"icons:{family}", "action", template, "secondary"),
              padding=w.pad(0, t.SPACE_2), valign="Center")
    return row
