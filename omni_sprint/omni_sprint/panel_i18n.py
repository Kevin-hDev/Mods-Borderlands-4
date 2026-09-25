"""One language lookup for the settings window, with English fallback."""

from . import panel_en, panel_fr


def text(key, language):
    source = panel_fr.TEXT if language == "FR" and key in panel_fr.TEXT else panel_en.TEXT
    return source[key]


def option_text(option, language):
    if language == "FR" and option.identifier in panel_fr.OPTIONS:
        return panel_fr.OPTIONS[option.identifier]
    return option.display_name, option.description


def group_text(group, key, language):
    return panel_fr.GROUPS[key] if language == "FR" else group.description


def number(option, value):
    digits = 0 if option.is_integer else max(0, len(str(option.step).rstrip("0").split(".")[-1]))
    return f"{value:.{digits}f}"
