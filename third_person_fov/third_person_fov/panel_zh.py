"""Simplified Chinese camera window labels from the common camera vocabulary."""

from .panel_camera_pages import page_texts
from .panel_camera_text import ZH as CAMERA, ZH_OPTIONS
from .panel_common_zh import TEXT as COMMON

TEXT = {**COMMON, **CAMERA}
GROUPS = page_texts(CAMERA)
OPTIONS = ZH_OPTIONS
