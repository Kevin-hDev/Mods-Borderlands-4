"""The bar's words, in the window's language (decision 62): English by default, French the second, as every menu of
Kevin's mods. The languages are the window's codes (panel_preferences.py). HORDE is how many enemies follow the player
(Kevin, 2026-10-14: « le nombre d'ennemis qui suivent le joueur en temps réel »), the same word in both."""

ENGLISH, FRENCH = "EN", "FR"
LANGUAGES = (ENGLISH, FRENCH)
_BAR = {
    ENGLISH: "KILLS {kills}   DEATHS {deaths}   HORDE {horde}   {clock}",
    FRENCH: "TUÉS {kills}   MORTS {deaths}   HORDE {horde}   {clock}",
}


def clock(seconds: float) -> str:
    """A time played as 04:37; past an hour, 1:02:05. Seconds are cut, never rounded up."""
    hours, rest = divmod(int(max(0.0, seconds)), 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


def bar(language: str, kills: int, deaths: int, horde: int, seconds: float) -> str:
    """The bar's words in that language; English for a language the mod does not have."""
    return _BAR.get(language, _BAR[ENGLISH]).format(kills=kills, deaths=deaths, horde=horde, clock=clock(seconds))
