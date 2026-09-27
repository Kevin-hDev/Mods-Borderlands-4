"""Standalone camera window: shared camera and frame vocabulary."""

from .panel_camera_text import EN as CAMERA
from .panel_common_en import TEXT as COMMON

TEXT = {**COMMON, **CAMERA,
        "camera_elsewhere": "Another mod controls the camera: set it in that mod's menu."}
