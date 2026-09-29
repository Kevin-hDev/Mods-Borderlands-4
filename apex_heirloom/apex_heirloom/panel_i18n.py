"""One lookup with English fallback; saved key identifiers are never translated."""

from . import panel_en, panel_fr


def text(key, language):
    if language == "FR" and key in panel_fr.TEXT:
        return panel_fr.TEXT[key]
    return panel_en.TEXT[key]


def option_text(option, language):
    if language == "FR" and option.identifier in panel_fr.OPTIONS:
        return panel_fr.OPTIONS[option.identifier]
    return option.display_name, option.description


def group_text(group, key, language):
    return panel_fr.GROUPS[key] if language == "FR" else group.description


def number(option, value):
    # Figures only, no unit: Kevin's choice on 2026-09-21 (« juste des valeurs en chiffres »).
    digits = 0 if option.is_integer else max(0, len(str(option.step).rstrip("0").split(".")[-1]))
    return f"{value:.{digits}f}"
