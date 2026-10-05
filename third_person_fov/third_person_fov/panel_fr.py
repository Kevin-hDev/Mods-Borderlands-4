"""French camera window labels from the common camera vocabulary."""

from .panel_camera_text import FR as CAMERA, FR_OPTIONS
from .panel_common_fr import TEXT as COMMON

TEXT = {**COMMON, **CAMERA}
GROUPS = {"camera": CAMERA["camera_desc"]}
OPTIONS = FR_OPTIONS
