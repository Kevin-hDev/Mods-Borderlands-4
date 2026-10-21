"""Japanese camera window labels from the common camera vocabulary."""

from .panel_camera_pages import page_texts
from .panel_camera_text import JA as CAMERA, JA_OPTIONS
from .panel_common_ja import TEXT as COMMON

TEXT = {**COMMON, **CAMERA}
GROUPS = page_texts(CAMERA)
OPTIONS = JA_OPTIONS
