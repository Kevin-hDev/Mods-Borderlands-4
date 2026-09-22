"""Validated settings transactions; Apex Movement's SDK options are the authority."""

import math

from . import menu, panel_preferences as prefs, report


class Model:
    def __init__(self, mod):
        self.mod = mod
        self.groups = tuple(menu.MENU)
        self.pages = tuple(group.identifier.removesuffix("_menu") for group in self.groups)
        self.options = {option.identifier: option for group in self.groups for option in group.children}
        self._undo = ()

    @property
    def language(self):
        return "FR" if prefs.french.value is True else "EN"

    @property
    def page(self):
        index = prefs.last_page.value
        valid = (type(index) in (int, float) and math.isfinite(index) and int(index) == index
                 and 0 <= index < len(prefs.PAGE_KEYS))
        saved = prefs.PAGE_KEYS[int(index)] if valid else None
        return saved if saved in self.pages else self.pages[0]

    @property
    def can_undo(self):
        return bool(self._undo)

    def save(self, changes):
        previous = tuple((option, option.value) for option, _ in changes)
        try:
            for option, value in changes:
                option.value = value
            self.mod.save_settings()
        except Exception:
            for option, value in previous:
                option.value = value
            try:
                self.mod.save_settings()
            except Exception:
                report.error_once("panel:save", "Settings could not be saved. Please retry.")
            return False
        return True

    def change_language(self, value):
        return value in prefs.LANGUAGES and self.save(((prefs.french, value == "FR"),))

    def change_page(self, value):
        if type(value) is not str or value not in self.pages:
            return False
        wanted = prefs.PAGE_KEYS.index(value)
        return wanted == prefs.last_page.value or self.save(((prefs.last_page, wanted),))

    @staticmethod
    def normalize(option, value):
        if type(option.default_value) is bool:
            if type(value) is not bool:
                raise ValueError("Invalid switch")
            return value
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError("Invalid number")
        if not option.min_value <= value <= option.max_value:
            raise ValueError("Out of bounds")
        steps = round((value - option.min_value) / option.step)
        result = min(option.max_value, max(option.min_value, option.min_value + steps * option.step))
        return int(round(result)) if option.is_integer else round(result, 6)

    def write(self, values):
        if type(values) is not dict or not 0 < len(values) <= len(self.options):
            return False
        try:
            changes = tuple((self.options[key], self.normalize(self.options[key], value))
                            for key, value in values.items())
        except (KeyError, TypeError, ValueError, OverflowError):
            return False
        if not self.save(changes):
            return False
        self._undo = ()
        return True

    def restore(self):
        previous = tuple((option, option.value) for option in self.options.values())
        if not self.save(tuple((option, option.default_value) for option, _ in previous)):
            return False
        self._undo = previous
        return True

    def undo(self):
        if not self._undo or not self.save(self._undo):
            return False
        self._undo = ()
        return True

    def toggle_enabled(self):
        previous = self.mod.is_enabled
        try:
            (self.mod.disable if previous else self.mod.enable)()
            self.mod.save_settings()
        except Exception:
            try:
                (self.mod.enable if previous else self.mod.disable)()
                self.mod.save_settings()
            except Exception:
                report.error_once("panel:enable", "Could not restore the mod state. Please retry.")
            return False
        return self.mod.is_enabled != previous
