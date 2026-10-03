"""English Benefix Ohm Attack texts: Apex Grapple's words for the page name, the icons and the reset of the COMMANDS page
(panel_controls_text.py), the rest this mod's own. A setting's name and sentence are its option's (settings.py)."""

from .panel_common_en import TEXT as COMMON
from .panel_controls_text import EN as CONTROLS

TEXT = {
    **COMMON, **CONTROLS, "beam": "BEAM", "no_key": "NONE",
    # The BEAM page's second card (menu.CARDS).
    "energy": "ENERGY",
    "energy_desc": "The beam has its own energy, 100 of it. Empty, the beam stops.",
    # The LOCK page, and its second card.
    "lock": "LOCK",
    "bounce": "BOUNCE",
    "bounce_desc": "The beam jumps from its target to a second enemy.",
    # The COMMANDS page's card, each row worded by its device (sketch C).
    "command_fire": "FIRE THE BEAM",
    "command_fire_desc": "The key to hold to fire the beam. None by default: choose yours.",
    "keyboard": "KEYBOARD / MOUSE", "controller": "CONTROLLER",
    "change_keyboard": "CHOOSE A KEY", "change_controller": "CHOOSE A BUTTON",
    "press_keyboard": "PRESS A KEY", "press_controller": "PRESS A BUTTON",
    "escape_hint": "Esc cancels key capture. The console key is reserved.",
    "controls_reset": "Default controls restored.",
    # Why a key was not saved, each its own cause (command_keys.py).
    "wheel_key": "Not saved: the mouse wheel cannot be held. Previous key kept.",
    "invalid_keyboard": "Not saved: choose a keyboard key or a mouse button. Previous key kept.",
    "invalid_controller": "Not saved: choose a controller button. Previous button kept.",
}
# The names the element's row writes between its arrows (panel_choices.label), by the menu's own names
# (settings.ELEMENTS).
CHOICES = {"Fire": "Fire", "Shock": "Shock", "Corrosive": "Corrosive", "Cryo": "Cryo", "Radiation": "Radiation",
           "Kinetic": "Kinetic"}
