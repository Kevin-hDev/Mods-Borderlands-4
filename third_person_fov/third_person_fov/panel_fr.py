"""French camera window labels from the common camera vocabulary."""

from .panel_camera_pages import page_texts
from .panel_camera_text import FR as CAMERA, FR_OPTIONS
from .panel_common_fr import TEXT as COMMON

# The key that opens this window in game (open_key.py, panel_open_key.py).
TEXT = {**COMMON, **CAMERA,
        "command_open_window": "RACCOURCI DU MENU",
        "command_open_window_desc": "Ouvre cette fenêtre en jeu, et la ferme.",
        "open_key_command": "Cette touche sert déjà à une commande de caméra : choisis-en une autre.",
        "key_opens_window": "Cette touche ouvre cette fenêtre (RACCOURCI DU MENU) : choisis-en une autre."}
GROUPS = page_texts(CAMERA)
OPTIONS = FR_OPTIONS
