"""The key that opens a camera mod's window in game, and closes it (Kevin, 2026-10-18): F10 for Apex Movement's full
pack, F7 for Third Person & FOV, none for Omni Sprint (docs/mokup/menu_mods/decisions.md). Each mod makes its one
OpenKey in its camera settings, beside its camera commands; the window finds it there (camera_control_config.OPEN_KEY).

Its one authority is a hidden option of the settings file, written through the window's settings transaction; the
SDK's keybind is given its key from it (align), at start and whenever the window polls. Taken from It Follows'
open_key.py; Third Person & FOV's F7 seen working in game on 2026-10-18.

The window it opens closes with it too, read as Windows sees it, as Escape is (control_escape.py), when its Unreal
name has a Windows key (control_console_keys.KEY_NAMES). Opened on the press: the release then reaches the window,
never the game, and the watch waits for the key to be up first (closer)."""

from mods_base import HiddenOption, keybind

from . import control_console_keys, report
from .control_escape import EscapeWatch

try:
    from .apex_camera_runtime.key_option import normalize_keyboard_key
except ModuleNotFoundError as error:
    if error.name != f"{__package__}.apex_camera_runtime":
        raise
    from apex_camera_runtime.key_option import normalize_keyboard_key


class OpenKey:
    def __init__(self, default, name, commands):
        """default: the key at first; name: the mod's, as the game's mod list shows it; commands: its camera
        commands."""
        self.default, self.commands = default, commands
        self.option = HiddenOption("open_key", default)
        self.bind = keybind("open_window", default, self._pressed, display_name=f"Open {name}",
                            description=f"The key that opens {name}'s window in game.", is_hidden=True)

    def _pressed(self):
        from . import control_window
        report.note(f"open key pressed: {self.bind.key}")
        control_window.start()

    @staticmethod
    def normalize(name):
        """A keyboard key's Unreal name, or None for no key. ValueError for anything else, and for the keys the camera
        commands refuse too: Escape and the left button close and click the window, Tilde opens the console."""
        return normalize_keyboard_key(name)

    def chosen(self):
        """The chosen key, None when the player chose none; the default for a value the file holds that is no key."""
        try:
            return self.normalize(self.option.value)
        except ValueError:
            return self.default

    def key(self):
        """The key that opens the window: the chosen one, unless a camera command had it before this key existed (a
        camera key saved as F7): the command keeps it and this one does nothing, as one press never does two things.
        The window then shows NONE here, and the player chooses another."""
        wanted = self.chosen()
        return None if wanted is not None and wanted in {item.value for item in self.commands.options} else wanted

    def align(self):
        """The SDK's keybind given the option's key, when they differ; whether it was."""
        if self.bind.key == self.key():
            return False
        self.bind.key = self.key()
        report.note(f"open key bound: {self.bind.key}")
        return True

    def closer(self):
        """The watch that closes the window with the key that opens it, deaf until the key is first up: opened by its
        press, the window must not close at its release. None without a key, or when Windows has no fixed key for
        it."""
        code = control_console_keys.KEY_NAMES.get(self.key())
        if code is None:
            return None
        watch = EscapeWatch(key=code)
        watch.muted = True
        return watch
