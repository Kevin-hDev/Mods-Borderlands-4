"""French camera window labels from the common camera vocabulary."""

from .panel_camera_pages import page_texts
from .panel_camera_text import FR as CAMERA, FR_OPTIONS
from .panel_common_fr import TEXT as COMMON

TEXT = {**COMMON, **CAMERA}
GROUPS = page_texts(CAMERA)
OPTIONS = FR_OPTIONS
