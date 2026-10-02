"""Validated settings transactions; Apex Movement's SDK options are the authority."""

import math

from mods_base import KeybindOption

from . import menu, pack, panel_preferences as prefs, report
from . import panel_toggle
from .panel_transaction import Transaction


class Model:
    # The line the window shows when the ENABLED switch did not take.
    toggle_notice = panel_toggle.FAILED

    def __init__(self, mod):
        self.mod = mod
        self.groups = tuple(menu.MENU)
        self.pages = tuple(group.identifier.removesuffix("_menu") for group in self.groups)
        movement = {option.identifier: option for group in self.groups for option in group.children}
        self.camera_options, self.command_options = {}, {}
        self.command_actions = None
        if pack.is_full():
            # Camera belongs to the full pack; separate movement files must remain independent.
            from . import camera_settings
            from .camera_control_actions import Actions
            self.camera_options = {option.identifier: option for option in camera_settings.VISIBLE}
            self.command_options = {option.identifier: option for option in camera_settings.commands.options}
            self.command_actions = Actions(camera_settings.commands, mod)
            self.pages += ("commands",)
        self.options = {**movement, **self.camera_options}
        self._undo, self._command_undo = (), {}
        self._command_plan = None
        self.transaction = Transaction(mod, report.error_once)

    @property
    def language(self):
        return "FR" if prefs.french.value is True else "EN"

    @property
    def page(self):
        index = prefs.last_page.value
        valid = (type(index) in (int, float) and math.isfinite(index) and int(index) == index
                 and 0 <= index < len(prefs.PAGE_KEYS))
        saved = prefs.PAGE_KEYS[int(index)] if valid else None
        return saved if saved in (*self.pages, "options") else self.pages[0]

    @property
    def can_undo(self):
        return bool(self._undo)

    @property
    def controller_icons(self):
        return prefs.controller_icons.value

    def save(self, changes, kind="save", previous=None):
        snapshot = (tuple((option, option.value) for option, _ in changes)
                    if previous is None else tuple(previous))
        return self._complete(self.transaction.start(changes, snapshot, kind))

    def _complete(self, outcome):
        if outcome is None:
            return None
        kind, previous, success = outcome
        if success and kind == "restore":
            self._undo = previous
        elif success and kind in ("write", "undo"):
            self._undo = ()
        return success

    def advance(self):
        outcome = self.transaction.advance()
        if outcome is None:
            return None
        if self._command_plan is not None:
            if self._command_plan[0] == "compensate":
                self._complete(outcome)
                self._command_plan = None
                return "failed"
            return self._finish_global(outcome, label=True)
        kind = outcome[0]
        success = self._complete(outcome)
        return {"restore": "restored", "undo": "undone", "write": "saved"}.get(
            kind, "saved") if success else "failed"

    def cancel_transaction(self):
        if not self.transaction.pending:
            return True
        outcome = self.transaction.cancel()
        if outcome is None:
            return False
        self._complete(outcome)
        return True

    def change_language(self, value):
        return value in prefs.LANGUAGES and self.save(((prefs.french, value == "FR"),))

    def change_controller_icons(self, value):
        return value in prefs.CONTROLLER_ICONS and self.save(((prefs.controller_icons, value),))

    def change_page(self, value):
        if type(value) is not str or value not in (*self.pages, "options"):
            return False
        wanted = prefs.PAGE_KEYS.index(value)
        return wanted == prefs.last_page.value or self.save(((prefs.last_page, wanted),))

    @staticmethod
    def normalize(option, value):
        if isinstance(option, KeybindOption):
            # Every file ships shortcut_key: the walk key lives in the separate Apex Auto Sprint file too.
            from .shortcut_key import normalize_keyboard_key
            return normalize_keyboard_key(value)
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
        return self.save(changes, "write")

    def write_commands(self, values):
        if not self._commands_ready():
            return False
        success = self.command_actions.apply(values)
        if success:
            self._undo, self._command_undo = (), {}
        return success

    def assign_command(self, action, device, key):
        if not self._commands_ready():
            return False
        success = self.command_actions.assign(action, device, key)
        if success:
            self._undo, self._command_undo = (), {}
        return success

    def default_commands(self):
        if not self._commands_ready():
            return False
        success = self.command_actions.defaults()
        if success:
            self._undo, self._command_undo = (), {}
        return success

    def _commands_ready(self):
        return (self.command_actions is not None and not self.transaction.pending
                and self._command_plan is None)

    def restore(self):
        memory = ()
        if self.command_actions is not None:
            from .camera_control_config import MEMORY_OPTIONS
            memory = MEMORY_OPTIONS
        previous = tuple((option, option.value) for option in (*self.options.values(), *memory))
        commands = self.command_actions.snapshot() if self.command_actions else {}
        desired = self.command_actions.commands.defaults() if self.command_actions else {}
        return self._start_global(tuple((option, option.default_value) for option, _ in previous),
                                  "restore", previous, desired, commands)

    def undo(self):
        if not self._undo:
            return False
        previous = tuple((option, option.value) for option, _ in self._undo)
        commands = self.command_actions.snapshot() if self.command_actions else {}
        return self._start_global(self._undo, "undo", previous, self._command_undo, commands)

    def _start_global(self, changes, kind, previous, command_values, previous_commands):
        self._command_plan = (kind, previous, command_values, previous_commands, self._undo)
        outcome = self.transaction.start(changes, previous, kind)
        if outcome is None:
            return None
        return self._finish_global(outcome, label=False)

    def _finish_global(self, outcome, label):
        kind, previous, command_values, previous_commands, former_undo = self._command_plan
        success = self._complete(outcome)
        if success and self.command_actions is not None:
            success = self.command_actions.apply(command_values)
        if success:
            if kind == "restore":
                self._command_undo = previous_commands
            elif kind == "undo":
                self._command_undo = {}
            self._command_plan = None
        else:
            self._undo = () if kind == "restore" else former_undo
            current = tuple((option, option.value) for option, _ in previous)
            compensation = self.transaction.start(previous, current, "compensate")
            if compensation is None:
                self._command_plan = ("compensate", (), {}, {}, ())
                return None
            self._complete(compensation)
            self._command_plan = None
        if not label:
            return success
        return {"restore": "restored", "undo": "undone"}[kind] if success else "failed"

    def toggle_enabled(self):
        if self.transaction.pending:
            return None
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
                report.error_once("panel:enable", "Could not restore the mod state. Please retry.")
            return False
        return self.mod.is_enabled != previous
