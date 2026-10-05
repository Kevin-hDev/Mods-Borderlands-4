"""SDK-backed framing choices; menu's existing Undo owns the restoration snapshot."""
from mods_base import BoolOption, SliderOption

from .framing_catalog import (CUSTOM_SUFFIX, GROUPS, INVALID_SETTING_NOTE,
                              OPTION_PREFIX, group)


class FramingSlider(SliderOption):
    def confirm_write(self, *, restoring=False):
        return self.framing_owner.confirm(restoring)


class FramingOrigin(BoolOption):
    def confirm_write(self, *, restoring=False):
        return self.framing_owner.confirm(restoring)


class FramingOptions:
    def __init__(self, note=None):
        self.note = note
        # Inactive mods store choices; an active adapter binds the live authority.
        self.confirm = lambda _restoring=False: True
        self._reported = [False for _ in GROUPS]
        values = []
        for definition in GROUPS:
            identifier = OPTION_PREFIX + definition.key
            values.append(FramingSlider(identifier, definition.default,
                                       definition.minimum, definition.maximum,
                                       step=definition.step, is_integer=True,
                                       is_hidden=True, display_name=definition.title))
            values.append(FramingOrigin(identifier + CUSTOM_SUFFIX, False, is_hidden=True))
        self.options = tuple(values)
        for option in self.options:
            option.framing_owner = self

    def _index(self, key):
        definition = group(key)
        return GROUPS.index(definition)

    @staticmethod
    def _valid(definition, value, custom):
        return (definition.valid(value) and type(custom) is bool
                and (custom or any(value == preset for _, preset in definition.presets)))

    def read(self, key):
        index = self._index(key)
        value, custom = (option.value for option in self.options[index * 2:index * 2 + 2])
        definition = GROUPS[index]
        if not self._valid(definition, value, custom):
            if not self._reported[index] and self.note is not None:
                self.note(INVALID_SETTING_NOTE)
            self._reported[index] = True
            return definition.default, False
        self._reported[index] = False
        return value, custom

    def snapshot(self):
        return tuple(self.read(definition.key) for definition in GROUPS)
