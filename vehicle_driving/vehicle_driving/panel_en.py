"""English Vehicle Driving page names and the CAMERA page's key card; setting text lives in settings.py."""

from .panel_common_en import TEXT as COMMON
from .panel_controls_text import EN as CONTROLS

# The CAMERA page's key card says what Apex Heirloom's COMMANDS page says: one way to choose a key in every menu.
TEXT = {
    **COMMON, **CONTROLS, "driving": "DRIVING", "handling": "HANDLING", "boost": "BOOST", "combat": "COMBAT",
    "camera": "CAMERA", "no_key": "NONE",
    "command_view": "CHANGE VIEW",
    "command_view_desc": "The key that goes to the next view, at the wheel.",
    "keyboard": "KEYBOARD / MOUSE", "controller": "CONTROLLER",
    "change_keyboard": "CHOOSE A KEY", "change_controller": "CHOOSE A BUTTON",
    "press_keyboard": "PRESS A KEY", "press_controller": "PRESS A BUTTON",
    "escape_hint": "Esc cancels key capture. The console key is reserved.",
    "controls_reset": "Default controls restored.",
    "invalid_keyboard": "Not saved: choose a keyboard key or a mouse button. Previous key kept.",
    "invalid_controller": "Not saved: choose a controller button. Previous button kept.",
}

# The views keep their own names in English (settings.VIEWS).
CHOICES: dict[str, str] = {}
