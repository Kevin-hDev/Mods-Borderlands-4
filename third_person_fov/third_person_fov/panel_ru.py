"""Russian camera window labels from the common camera vocabulary."""

from .panel_camera_pages import page_texts
from .panel_common_ru import TEXT as COMMON
from .panel_ru_texts import CAMERA, CAMERA_OPTIONS

TEXT = {**COMMON, **CAMERA}
GROUPS = page_texts(CAMERA)
OPTIONS = CAMERA_OPTIONS
