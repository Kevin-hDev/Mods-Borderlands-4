"""English Apex Heirloom texts: Apex Grapple's words for the page name, the icons and the reset of the COMMANDS page
(panel_controls_text.py), the rest this mod's own."""

from .panel_common_en import TEXT as COMMON
from .panel_controls_text import EN as CONTROLS

TEXT = {
    **COMMON, **CONTROLS, "heirloom": "HEIRLOOM", "holster": "HOLSTER", "no_key": "NONE",
    "applies": "Leave the menu and change weapons to apply the change.",
    "refused_part": "Another installed file already runs this part. Turn it off first.",
    # The COMMANDS page's cards (sketch I1, 2026-09-30), each row worded by its device, as the sketch.
    "command_put_away": "PUT AWAY",
    "command_put_away_desc": "The key that puts your weapon away, held or pressed. Greyed out while Holster is OFF.",
    "command_inspect": "ANIMATION",
    "command_inspect_desc": "Spin your heirloom in your hand while your weapon is put away. Greyed out while Heirloom "
                            "is OFF.",
    "keyboard": "KEYBOARD / MOUSE", "controller": "CONTROLLER",
    "change_keyboard": "CHOOSE A KEY", "change_controller": "CHOOSE A BUTTON",
    "press_keyboard": "PRESS A KEY", "press_controller": "PRESS A BUTTON",
    "escape_hint": "Esc cancels key capture. The console key is reserved.",
    "controls_reset": "Default controls restored.",
    # Why a key was not saved, each its own cause (command_keys.py).
    "duplicate_put_away": "Not saved: this key already puts your weapon away. Previous key kept.",
    "duplicate_inspect": "Not saved: this key already plays your heirloom's animation. Previous key kept.",
    "wheel_key": "Not saved: the mouse wheel changes weapons in the game. Previous key kept.",
    "invalid_keyboard": "Not saved: choose a keyboard key or a mouse button. Previous key kept.",
    "invalid_controller": "Not saved: choose a controller button. Previous button kept.",
}
# The names a choice's buttons and arrows write (panel_choices.label): the heirlooms, then their skins. The skins'
# are their game files', which Kevin keeps (2026-09-29: « pour les noms de skins on peut laisser comme ça »).
CHOICES = {"jakobs_knife": "Jakobs Knife", "axe": "Axe", "own": "Original", "hacker": "Hacker", "storm": "Storm",
           "blood": "Blood", "sports": "Sports", "moxxi": "Moxxi", "legendary_04": "Legendary 04"}
