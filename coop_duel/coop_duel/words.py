"""The duel's words outside the window, the message on the screen and the players' names when the game gives none, in
the language chosen in the window: the window's own texts (panel_en.py, panel_fr.py) are their one authority."""

from . import panel_i18n


def text(key: str, language: str) -> str:
    return panel_i18n.text(key, language)
