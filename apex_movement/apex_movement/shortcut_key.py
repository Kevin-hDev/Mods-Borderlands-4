"""The keyboard shortcut option, from its one source in the camera runtime.

Every file of the pack ships the runtime's key_option module, the separate movement files included (build tool), so
the walk key and the menu that captures a new key work in each of them.
"""

try:
    from .apex_camera_runtime.key_option import KeyboardKeybindOption, normalize_keyboard_key
except ModuleNotFoundError as error:
    if error.name != f"{__package__}.apex_camera_runtime":
        raise
    # The sources: the runtime sits beside the mod rather than inside its built file.
    from apex_camera_runtime.key_option import KeyboardKeybindOption, normalize_keyboard_key

__all__ = ("KeyboardKeybindOption", "normalize_keyboard_key")
