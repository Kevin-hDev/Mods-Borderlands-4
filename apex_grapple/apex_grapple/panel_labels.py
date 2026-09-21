"""Refresh texts and button states without rebuilding widgets or losing key capture state.

Selection shows as in the mockup: the chosen page and language become gold plates, never a "> " or "[EN]" mark.
"""

from . import panel_buttons as b, panel_i18n as i18n, panel_slider as s, panel_theme as t, panel_controls


def controls_summary(bindings, language):
    return panel_controls.summary(bindings, language)


def _buttons(form, widgets, language):
    for name in ("close", "restore", "undo", "reset"):
        widgets[f"{name}_label"].SetText(i18n.text("reset_controls" if name == "reset" else name, language))
    widgets["undo"].SetIsEnabled(form.model.can_undo)
    b.paint(widgets, "undo", "secondary" if form.model.can_undo else "disabled")
    for lang in ("EN", "FR"):
        widgets[f"{lang}_label"].SetText(lang)
        b.paint(widgets, lang, "lang_on" if lang == language else "lang_off")
    for index, key in enumerate(t.PAGES):
        widgets[f"nav:{key}_label"].SetText(i18n.text(key, language))
        b.paint(widgets, f"nav:{key}", "nav_on" if form.page == index else "nav_off")
    enabled = form.model.mod.is_enabled
    widgets["enabled_label"].SetText(i18n.text("enabled" if enabled else "disabled", language))
    b.paint(widgets, "enabled", "on" if enabled else "off")
    widgets["two_label"].SetText(i18n.text("on" if form.two else "off", language))
    b.paint(widgets, "two", "on" if form.two else "off")


def apply(form, widgets):
    from . import __version__
    language = form.model.language
    _buttons(form, widgets, language)
    widgets["tag"].SetText(f"{i18n.text('by', language)} {t.AUTHOR}")
    widgets["settings_caption"].SetText(i18n.text("settings", language))
    widgets["meta"].SetText(f"{i18n.text('version', language)} {__version__} · {i18n.text('by', language)} {t.AUTHOR}")
    for group, key in zip(form.model.groups, t.PAGES):
        widgets[f"heading:{key}"].SetText(i18n.text(key, language))
        widgets[f"group:{key}"].SetText(i18n.group_text(group, key, language))
    widgets["heading:controls"].SetText(i18n.text("controls", language))
    widgets["group:controls"].SetText(i18n.text("controls_intro", language))
    for key, option in form.model.options.items():
        title, description = i18n.option_text(option, language)
        widgets[f"label:{key}"].SetText(title.upper())
        widgets[f"description:{key}"].SetText(description)
    widgets["escape_hint"].SetText(i18n.text("escape_hint", language))
    widgets["two_text"].SetText(i18n.text("two", language).upper())
    for name in ("first", "second"):
        widgets[name].SetNoKeySpecifiedText(i18n.text(name, language))
        widgets[name].SetKeySelectionText(i18n.text("listening", language))
    widgets["status"].SetText(i18n.text("two_hint" if form.two else "one_hint", language))
    widgets["current"].SetText(controls_summary(form.bindings, language))
    widgets["notice"].SetText(i18n.text(form.notice, language))
    widgets["icons_label"].SetText(i18n.text("controller_icons", language))
    for family in ("PS5", "XSX"):
        widgets[f"icons:{family}_label"].SetText(i18n.text(family, language))
        b.paint(widgets, f"icons:{family}", "primary" if family == form.model.controller_icons else "secondary")
    form.key_display.summary(form, widgets)
    form.key_display.update(form, widgets)


def value(widgets, option, current, language):
    key = option.identifier
    if type(option.default_value) is bool:
        widgets[f"setting:{key}_label"].SetText(i18n.text("on" if current else "off", language))
        b.paint(widgets, f"setting:{key}", "on" if current else "off")
    else:
        s.show(widgets, option, current)
