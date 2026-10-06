"""Validated settings transactions; the existing SDK options remain authoritative."""

import math

from . import control_actions, control_config, settings
from .panel_preferences import LANGUAGES, language
from .panel_preferences import CONTROLLER_ICONS, controller_icons
from .panel_preferences import PAGES, last_page
from .panel_preferences import THEMES, theme
from . import panel_toggle

MAX_CHANGES = len(settings.ALL)


class Model:
    # The line the window shows when the ENABLED switch did not take.
    toggle_notice = panel_toggle.FAILED

    def __init__(self, mod):
        from . import menu
        self.mod = mod
        self.groups = (menu.shot, menu.pull, menu.release)
        self.controls = tuple(menu.hold.children)
        self.options = {option.identifier: option for option in settings.ALL}
        self._undo = ()

    @property
    def language(self):
        return language.value if language.value in LANGUAGES else language.default_value

    @property
    def can_undo(self):
        return bool(self._undo)

    @property
    def controller_icons(self):
        return controller_icons.value if controller_icons.value in CONTROLLER_ICONS else controller_icons.default_value

    def change_controller_icons(self, value):
        return value in CONTROLLER_ICONS and self.save(((controller_icons, value),))

    @property
    def page(self):
        return last_page.value if last_page.value in PAGES else last_page.default_value

    def change_page(self, value):
        if type(value) is not str or value not in PAGES:
            return False
        return value == last_page.value or self.save(((last_page, value),))

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
                from . import report
                report.error_once("panel:save", "Settings could not be saved. Please retry.")
            return False
        return True

    def change_language(self, value):
        return value in LANGUAGES and self.save(((language, value),))

    @property
    def theme(self):
        return theme.value if theme.value in THEMES else theme.default_value

    def change_theme(self, value):
        return value in THEMES and self.save(((theme, value),))

    def normalize(self, option, value):
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
        if type(values) is not dict or not 0 < len(values) <= MAX_CHANGES:
            return False
        try:
            changes = tuple((self.options[key], self.normalize(self.options[key], value))
                            for key, value in values.items())
            wanted = {option.identifier: value for option, value in changes}
            punch = wanted.get("punch_range", settings.punch_range.value)
            reach = wanted.get("grapple_range", settings.grapple_range.value)
            if punch >= reach:
                return False
        except (KeyError, TypeError, ValueError, OverflowError):
            return False
        if not self.save(changes):
            return False
        self._undo = ()
        return True

    def restore(self):
        options = (*settings.ALL, *control_config.ALL)
        previous = tuple((option, option.value) for option in options)
        if not control_actions.save_values(self.mod, tuple((o, o.default_value) for o in options)):
            return False
        # One bounded undo snapshot; the language is a preference, not a gameplay default.
        self._undo = previous
        return True

    def undo(self):
        if not self._undo or not control_actions.save_values(self.mod, self._undo):
            return False
        self._undo = ()
        return True

    def toggle_enabled(self):
        previous = self.mod.is_enabled
        try:
            (self.mod.disable if previous else self.mod.enable)()
            self.mod.save_settings()
        except Exception as error:
            self.toggle_notice = panel_toggle.notice(not previous, error)
            try:
                (self.mod.enable if previous else self.mod.disable)()
                self.mod.save_settings()
            except Exception:
                from . import report
                report.error_once("panel:enable", "Could not restore the mod state. Please retry.")
            return False
        return self.mod.is_enabled != previous
