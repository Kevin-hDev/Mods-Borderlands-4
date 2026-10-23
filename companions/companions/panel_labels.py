# Generated: the window Kevin's mods share, taken from Hunter Change's plain window, under Companions'
# names. Its comments may speak of other mods. Never edited by hand: docs/renforts/outils/menu_window.py
# writes this file.
"""Refresh the same button colours and text roles used by Grapple's window."""

from . import panel_buttons as b, panel_i18n as i18n, panel_slider as s, panel_theme as t
from . import panel_team, panel_theme_choice
from . import panel_size_choice
from .panel_header import language_button
from .panel_preferences import LANGUAGES


def apply(form, widgets):
    from . import __version__
    language = form.model.language
    for name in ("close",):
        widgets[f"{name}_label"].SetText(i18n.text(name, language))
    panel_size_choice.paint(widgets, form.model.window_size, language)
    panel_theme_choice.paint(widgets, form.model.theme, language)
    for lang in LANGUAGES:
        widgets[f"{lang}_label"].SetText(language_button(lang))
        b.paint(widgets, lang, "lang_on" if lang == language else "lang_off")
    for index, key in enumerate(form.model.pages):
        widgets[f"nav:{key}_label"].SetText(i18n.text(key, language))
        b.paint(widgets, f"nav:{key}", "nav_on" if form.page == index else "nav_off")
    enabled = form.model.mod.is_enabled
    widgets["enabled_label"].SetText(i18n.text("enabled" if enabled else "disabled", language))
    b.paint(widgets, "enabled", "on" if enabled else "off")
    widgets["tag"].SetText(f"{i18n.text('by', language)} {t.AUTHOR}")
    widgets["meta"].SetText(f"{i18n.text('version', language)} {__version__} · "
                            f"{i18n.text('by', language)} {t.AUTHOR}")
    for group, key in zip(form.model.groups, form.model.pages):
        widgets[f"heading:{key}"].SetText(i18n.text(key, language))
        widgets[f"group:{key}"].SetText(i18n.group_text(group, key, language))
    for key, option in form.model.options.items():
        title, description = i18n.option_text(option, language)
        widgets[f"label:{key}"].SetText(title.upper())
        widgets[f"description:{key}"].SetText(description)
    panel_team.paint(form, widgets, language)
    widgets["notice"].SetText(panel_team.notice(form, language))


def value(widgets, option, current, language):
    key = option.identifier
    if type(option.default_value) is bool:
        widgets[f"setting:{key}_label"].SetText(i18n.text("on" if current else "off", language))
        b.paint(widgets, f"setting:{key}", "on" if current else "off")
    else:
        s.show(widgets, option, current)
