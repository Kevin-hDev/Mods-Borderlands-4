"""The key that opens Third Person & FOV's window in game, F7 unless the player chose another, or none, on the
COMMANDS page (Kevin, 2026-10-18: « F7 c'est parfait »; docs/mokup/menu_mods/decisions.md, same day). Its one
authority is a hidden option of the settings file, written through the window's settings transaction; the SDK's
keybind is given its key from it (align), at start and whenever the window polls. Taken from It Follows' open_key.py,
its key seen working in game.

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

DEFAULT = "F7"

option = HiddenOption("open_key", DEFAULT)


def _pressed() -> None:
    from . import control_window
    report.note(f"open key pressed: {bind.key}")
    control_window.start()


bind = keybind("open_window", DEFAULT, _pressed, display_name="Open Third Person & FOV",
               description="The key that opens Third Person & FOV's window in game.", is_hidden=True)


def normalize(name: object) -> str | None:
    """A keyboard key's Unreal name, or None for no key. ValueError for anything else, and for the keys the camera
    commands refuse too: Escape and the left button close and click the window, Tilde opens the console."""
    return normalize_keyboard_key(name)


def chosen() -> str | None:
    """The chosen key, None when the player chose none; the default for a value the file holds that is no key."""
    try:
        return normalize(option.value)
    except ValueError:
        return DEFAULT


def key() -> str | None:
    """The key that opens the window: the chosen one, unless a camera command had it before this key existed (a
    camera key saved as F7): the command keeps it and this one does nothing, as one press never does two things
    (decisions.md, 2026-10-18). The window then shows NONE here, and the player chooses another."""
    from . import settings
    wanted = chosen()
    return None if wanted is not None and wanted in {item.value for item in settings.commands.options} else wanted


def align() -> bool:
    """The SDK's keybind given the option's key, when they differ; whether it was."""
    if bind.key == key():
        return False
    bind.key = key()
    report.note(f"open key bound: {bind.key}")
    return True


def closer() -> EscapeWatch | None:
    """The watch that closes the window with the key that opens it, deaf until the key is first up: opened by its
    press, the window must not close at its release. None without a key, or when Windows has no fixed key for it."""
    code = control_console_keys.KEY_NAMES.get(key())
    if code is None:
        return None
    watch = EscapeWatch(key=code)
    watch.muted = True
    return watch
