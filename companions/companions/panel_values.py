"""The SETTINGS page's values in words, as sketch A2 shows them: ×4 for the health, 30 % for the shield, NEVER at the
refill's left end then 45 s, +20 % for the speed, 45 s for the wait before coming back. The shared slider writes its
value and its two ends through number (menu_window_changes.py); the window's language is the one of its last paint
(use), which runs before the rows' values are written (panel_labels.apply, then value). Any other slider keeps the
shared window's number (panel_i18n.number)."""

from typing import Any

from . import panel_i18n as i18n, settings

# By slider: the text that writes its value, {value} the shared window's number.
WORDS = {settings.health.identifier: "value_times", settings.shield.identifier: "value_percent",
         settings.refill.identifier: "value_seconds", settings.speed.identifier: "value_bonus",
         settings.back.identifier: "value_seconds"}
_language = {"now": "EN"}


def use(language: str) -> None:
    _language["now"] = language


def number(option: Any, value: float) -> str:
    words = WORDS.get(option.identifier)
    if words is None:
        return i18n.number(option, value)
    language = _language["now"]
    if option.identifier == settings.refill.identifier and value <= settings.NEVER:
        return i18n.text("value_never", language)
    if words == "value_bonus" and value <= 0:
        words = "value_percent"
    return i18n.text(words, language).format(value=i18n.number(option, value))
