"""Standalone camera window: shared camera and frame vocabulary."""

from .panel_camera_text import EN as CAMERA
from .panel_common_en import TEXT as COMMON

# The key that opens this window in game (open_key.py, panel_open_key.py).
TEXT = {**COMMON, **CAMERA,
        "command_open_window": "MENU SHORTCUT",
        "command_open_window_desc": "Opens this window in game, and closes it.",
        "open_key_command": "This key is already a camera command's: choose another one.",
        "key_opens_window": "This key opens this window (MENU SHORTCUT): choose another one."}
