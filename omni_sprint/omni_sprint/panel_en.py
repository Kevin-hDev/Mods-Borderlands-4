"""English Omni Sprint texts: camera words from Apex Movement's menu, setting names from settings.py."""

from .panel_camera_text import EN as CAMERA
from .panel_common_en import TEXT as COMMON

# The page is named after the mod in both languages (Kevin, 2026-09-25): French falls back to this.
TEXT = {**COMMON, **CAMERA, "omni_sprint": "OMNI SPRINT",
        "camera_elsewhere": "Another mod controls the camera: set it in that mod's menu."}
