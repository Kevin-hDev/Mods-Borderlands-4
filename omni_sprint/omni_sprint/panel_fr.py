"""French Omni Sprint texts: camera words and setting names from Apex Movement's menu."""

from .panel_camera_text import FR as CAMERA, FR_OPTIONS
from .panel_common_fr import TEXT as COMMON

TEXT = {**COMMON, **CAMERA, "camera_elsewhere": "Un autre mod contrôle la caméra : règle-la dans son menu."}
GROUPS = {"omni_sprint": "Le sprint du jeu, dans toutes les directions.", "camera": CAMERA["camera_desc"]}
OPTIONS = {"omni_sprint": ("Sprint dans toutes les directions", "Sprinte aussi sur les côtés et en arrière."),
           **FR_OPTIONS}
