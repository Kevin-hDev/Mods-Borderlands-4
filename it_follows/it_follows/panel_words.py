"""How the window names a run's level, time limit, moment and end, in the language shown: one place, so that the RUN
page, the history and a run's result say them alike. A level is Level 1 to Level 5, never its number of enemies
(decisions 53 and 70)."""

import time

from . import levels, options, panel_choices, panel_i18n as i18n


def number(target: int) -> int | None:
    """The level's place among the levels, 1 to 5; None for a target the mod no longer has."""
    targets = list(levels.LEVELS)
    return targets.index(target) + 1 if target in targets else None


def level(target: int, language: str) -> str:
    """The level as its button names it: LEVEL 2."""
    return panel_choices.label(str(target), language, options.level)


def level_in_sentence(target: int, language: str) -> str:
    """The level inside a sentence: level 2."""
    return i18n.text("level_number", language).format(number=number(target) or target)


def limit(limit_s: float | None, language: str) -> str:
    """The time limit as its button names it: 30 MIN, UNLIMITED."""
    return panel_choices.label(options.duration_name(limit_s), language, options.duration)


def when(moment: int, language: str, now: float | None = None) -> str:
    """When a run began, in the player's local time: TODAY 14:32, YESTERDAY 23:05, OCT 12 20:15."""
    began = time.localtime(moment)
    today = time.localtime(time.time() if now is None else now)
    clock = i18n.text("clock_time", language).format(hour=began.tm_hour, minute=began.tm_min)
    days = (time.mktime(today[:3] + (0, 0, 0, 0, 0, -1)) - time.mktime(began[:3] + (0, 0, 0, 0, 0, -1))) / 86_400
    if round(days) == 0:
        return i18n.text("today", language).format(time=clock)
    if round(days) == 1:
        return i18n.text("yesterday", language).format(time=clock)
    month = i18n.text("months", language).split()[began.tm_mon - 1]
    return i18n.text("day", language).format(day=began.tm_mday, month=month, time=clock)


def end(name: str, language: str) -> str:
    return i18n.text(f"end:{name}", language)
