"""The camera actions exposed by the dedicated commands page."""

from typing import NamedTuple

from . import camera_settings

try:
    from .apex_camera_runtime.camera_commands import ACTIONS, CONTROLLER, KEYBOARD
    from .apex_camera_runtime.framing_catalog import GROUPS as FRAMING_GROUPS
except ModuleNotFoundError as error:
    if error.name != f"{__package__}.apex_camera_runtime":
        raise
    from apex_camera_runtime.camera_commands import ACTIONS, CONTROLLER, KEYBOARD
    from apex_camera_runtime.framing_catalog import GROUPS as FRAMING_GROUPS


class Command(NamedTuple):
    name: str
    keyboard: object
    controller: object


COMMANDS = tuple(Command(action.name,
                         camera_settings.commands.option(action.keyboard_id),
                         camera_settings.commands.option(action.controller_id))
                 for action in ACTIONS)
SLOTS = tuple((command.name, device) for command in COMMANDS
              for device in (KEYBOARD, CONTROLLER))
FRAMING_OPTIONS = camera_settings.framing
MEMORY_OPTIONS = (camera_settings.zoom.option, camera_settings.distance.option, *FRAMING_OPTIONS.options)
