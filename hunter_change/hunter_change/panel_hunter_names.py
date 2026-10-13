"""A hunter's name as the window writes it: a language's table may name the hunters (panel_zh.NAMES); otherwise the
name of hunters.py, which the English and French games share."""

from . import hunters, panel_i18n as i18n


def name(hunter: hunters.Hunter, language: str) -> str:
    return getattr(i18n.TABLES.get(language), "NAMES", {}).get(hunter.code, hunter.name)
