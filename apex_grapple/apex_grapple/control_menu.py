"""One visible entry opens the window; hidden storage preserves existing saved controls."""

from mods_base import ButtonOption, NestedOption

from . import control_actions as actions, control_config as config

TITLE = "Grapple controls"
DESCRIPTION = "Open the controls window to choose keys, mouse buttons or controller buttons."


def open_window(_button):
    from . import control_window
    control_window.start(return_to_menu=True)


MENU = ButtonOption("open_controls", display_name=TITLE, description=DESCRIPTION, on_press=open_window)
# Keep the old JSON identifiers and nesting: hiding the data avoids a settings migration.
STORAGE = NestedOption("controls_menu", [
    NestedOption(f"{device.name}_controls", list(device.options), is_hidden=True)
    for device in config.DEVICES
], is_hidden=True)
RESTORE = ButtonOption("restore_defaults", display_name="Restore defaults",
                       description="Restore all Apex Grapple settings and controls to their original defaults.",
                       on_press=actions.restore)
