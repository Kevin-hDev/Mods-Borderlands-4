"""Apex Heirloom's command cards, each with one keyboard/mouse and one controller row, from Apex Movement's
(outils/sync_menu_heirloom_commands.py)."""

from . import control_config as config, panel_buttons as b, panel_glyphs, panel_i18n as i18n
from . import panel_key_view as keys, panel_pages as p, panel_text as tx, panel_theme as t, panel_widgets as w


def _value(rows, widgets, name):
    box = w.new("HorizontalBox", rows)
    icon = keys.icon(box, widgets, f"value:{name}:icon")
    w.row(box, icon, valign="Center")
    widgets[f"value:{name}"] = tx.text(box, "", "gold", wrap=True)
    w.row(box, widgets[f"value:{name}"], padding=w.pad(0, 0, 0, t.SPACE_2), valign="Center")
    return box


def _device_row(rows, widgets, template, action, device):
    name = f"{action}:{device}"
    widgets[f"device:{name}"] = tx.text(rows, "", "label", wrap=True)
    selector = p.selector(rows, "", template)
    selector.SetAllowGamepadKeys(device == "controller")
    widgets[f"command:{name}"] = selector
    controls = w.new("HorizontalBox", rows)
    change = keys.selector(controls, widgets, f"command:{name}")
    # This field carries one short action, unlike Grapple's wide two-key selector: keep room for the saved value.
    change.SetWidthOverride(float(t.KEY_CHANGE_WIDTH))
    w.row(controls, change, valign="Center")
    w.row(controls, b.button(controls, widgets, f"clear:{name}", "action", template, "secondary"),
          padding=w.pad(0, 0, 0, t.SPACE_2), valign="Center")
    p._row(rows, widgets[f"device:{name}"], controls, _value(rows, widgets, name))


def page(owner, model, widgets, template):
    page, body = p.scrolling_body(owner, template)
    for command in config.COMMANDS:
        rows = p.card(body, widgets, f"command_{command.name}")
        # Greyed as a whole while its part is off (the mod's menu.COMMANDS_DEPEND_ON).
        widgets[f"card:command_{command.name}"] = rows
        for device in ("keyboard", "controller"):
            _device_row(rows, widgets, template, command.name, device)
    rows = p.plain_card(body)
    w.column(rows, keys.family_choice(rows, widgets, template), padding=w.pad(t.SPACE_2, 0))
    w.column(rows, b.button(rows, widgets, "commands_reset", "action", template, "secondary"), halign="Left")
    widgets["commands_status"] = tx.text(rows, "", "status", wrap=True)
    w.column(rows, widgets["commands_status"], padding=w.pad(t.SPACE_3, 0))
    widgets["escape_hint"] = tx.text(rows, "", "hint", wrap=True)
    w.column(rows, widgets["escape_hint"], padding=w.pad(t.SPACE_3, 0))
    return page


def refresh(form, widgets, catalogue):
    language, family = form.model.language, form.model.controller_icons
    for command in config.COMMANDS:
        key = f"command_{command.name}"
        widgets[f"heading:{key}"].SetText(i18n.text(key, language))
        widgets[f"group:{key}"].SetText(i18n.text(f"{key}_desc", language))
        for device, option in (("keyboard", command.keyboard), ("controller", command.controller)):
            name = f"{command.name}:{device}"
            widgets[f"device:{name}"].SetText(i18n.text(device, language))
            widgets[f"clear:{name}_label"].SetText(i18n.text("no_key", language))
            widgets[f"command:{name}"].SetNoKeySpecifiedText(i18n.text(f"change_{device}", language))
            widgets[f"command:{name}"].SetKeySelectionText(i18n.text(f"press_{device}", language))
            _show_value(widgets, name, option.value, family, language, catalogue)
    widgets["commands_reset_label"].SetText(i18n.text("reset_controls", language))
    widgets["escape_hint"].SetText(i18n.text("escape_hint", language))
    widgets["commands_status"].SetText(i18n.text(form.command_form.notice, language))
    widgets["icons_label"].SetText(i18n.text("controller_icons", language))
    for choice in ("PS5", "XSX"):
        widgets[f"icons:{choice}_label"].SetText(i18n.text(choice, language))
        b.paint(widgets, f"icons:{choice}", "primary" if choice == family else "secondary")


def _show_value(widgets, name, value, family, language, catalogue):
    image, label = widgets[f"value:{name}:icon"], widgets[f"value:{name}"]
    brush = catalogue.brush(family, value) if value and name.endswith(":controller") else None
    image.SetVisibility(w.enum("ESlateVisibility", "HitTestInvisible" if brush else "Collapsed"))
    if brush:
        image.SetBrush(brush)
    label.SetVisibility(w.enum("ESlateVisibility", "Collapsed" if brush else "HitTestInvisible"))
    label.SetText(panel_glyphs.label(value, family, language) if value else i18n.text("no_key", language))
