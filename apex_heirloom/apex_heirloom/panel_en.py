"""English Apex Heirloom texts: the CONTROLS page's words from Apex Grapple's menu, the rest this mod's own."""

from .panel_common_en import TEXT as COMMON
from .panel_controls_text import EN as CONTROLS

# Where one key per device differs from Grapple's two slots and game controls, the words are this mod's own.
TEXT = {
    **COMMON, **CONTROLS, "heirloom": "HEIRLOOM", "holster": "HOLSTER", "first": "CHOOSE A KEY", "no_key": "None",
    "applies": "Leave the menu and change weapons to apply the change.",
    "refused_part": "Another installed file already runs this part. Turn it off first.",
    "controls_intro": "Choose a key: keyboard, mouse or controller.",
    "escape_hint": "Esc cancels key capture. The console key is reserved.",
    "invalid_keys": "Not saved. Choose a keyboard key, a mouse button or a controller button.",
    "controls_reset": "Default controls restored.",
}
# The names a choice's buttons and arrows write (panel_choices.label): the heirlooms, then their skins. The skins'
# are their game files', which Kevin keeps (2026-09-29: « pour les noms de skins on peut laisser comme ça »).
CHOICES = {"jakobs_knife": "Jakobs Knife", "axe": "Axe", "own": "Original", "hacker": "Hacker", "storm": "Storm",
           "blood": "Blood", "sports": "Sports", "moxxi": "Moxxi", "legendary_04": "Legendary 04"}
