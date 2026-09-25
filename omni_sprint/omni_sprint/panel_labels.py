"""Refresh the same button colours and text roles used by Grapple's window."""

from . import panel_buttons as b, panel_i18n as i18n, panel_shortcut as sc, panel_slider as s, panel_theme as t


def apply(form, widgets):
    from . import __version__
    language = form.model.language
    for name in ("close", "restore", "undo"):
        widgets[f"{name}_label"].SetText(i18n.text(name, language))
    widgets["undo"].SetIsEnabled(form.model.can_undo)
    b.paint(widgets, "undo", "secondary" if form.model.can_undo else "disabled")
    for lang in ("EN", "FR"):
        widgets[f"{lang}_label"].SetText(lang)
        b.paint(widgets, lang, "lang_on" if lang == language else "lang_off")
    for index, key in enumerate(form.model.pages):
        widgets[f"nav:{key}_label"].SetText(i18n.text(key, language))
        b.paint(widgets, f"nav:{key}", "nav_on" if form.page == index else "nav_off")
    enabled = form.model.mod.is_enabled
    widgets["enabled_label"].SetText(i18n.text("enabled" if enabled else "disabled", language))
    b.paint(widgets, "enabled", "on" if enabled else "off")
    widgets["tag"].SetText(f"{i18n.text('by', language)} {t.AUTHOR}")
    widgets["settings_caption"].SetText(i18n.text("settings", language))
    widgets["meta"].SetText(f"{i18n.text('version', language)} {__version__} · "
                            f"{i18n.text('by', language)} {t.AUTHOR}")
    for group, key in zip(form.model.groups, form.model.pages):
        widgets[f"heading:{key}"].SetText(i18n.text(key, language))
        elsewhere = form.model.camera_elsewhere and key == "camera"
        widgets[f"group:{key}"].SetText(i18n.text("camera_elsewhere", language) if elsewhere
                                        else i18n.group_text(group, key, language))
    for key, option in form.model.options.items():
        if sc.is_shortcut(option):
            sc.texts(widgets, key, language)
            continue
        title, description = i18n.option_text(option, language)
        widgets[f"label:{key}"].SetText(title.upper())
        widgets[f"description:{key}"].SetText(description)
    widgets["notice"].SetText(i18n.text(form.notice, language))


def value(widgets, option, current, language):
    key = option.identifier
    if sc.is_shortcut(option):
        sc.show_key(widgets[f"key:{key}"], current)
    elif type(option.default_value) is bool:
        widgets[f"setting:{key}_label"].SetText(i18n.text("on" if current else "off", language))
        b.paint(widgets, f"setting:{key}", "on" if current else "off")
    else:
        s.show(widgets, option, current)
