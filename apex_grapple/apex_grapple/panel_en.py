"""English interface messages; option names/descriptions come from their SDK options."""

TEXT = {
    "shot": "THE SHOT", "pull": "THE PULL", "release": "LETTING GO", "look": "LOOK", "controls": "CONTROLS",
    "close": "CLOSE", "restore": "RESTORE DEFAULTS", "undo": "UNDO RESET",
    "enabled": "ENABLED", "disabled": "DISABLED", "on": "ON", "off": "OFF",
    "by": "BY", "version": "VERSION", "settings": "SETTINGS",
    "ready": "Changes are saved automatically. Close returns to the mod list.",
    "saved": "Saved.", "failed": "Settings could not be saved. Please try again.",
    "rollback_abandoned": "The change was cancelled. Recovery could not be confirmed; restart the game before changing settings.",
    "toggle_failed": "The mod could not be switched on or off. Nothing was changed. The reason is in unrealsdk.log.",
    # The update notes' pop-up (panel_updates.py).
    "updates_title": "UPDATE {version}", "updates_count": "{page} / {pages}", "updates_next": "NEXT",
    "refused": "Assignment refused. This input is reserved or already used.",
    "restored": "Default settings restored. You can undo this reset.", "undone": "Previous settings restored.",
    "controls_intro": "Choose a slot, then press a keyboard, mouse or controller button. Complete choices save automatically.",
    "two": "Two keys held together", "first": "1. CHOOSE A KEY", "second": "2. CHOOSE SECOND KEY",
    "listening": "PRESS YOUR KEY NOW", "reset_controls": "RESET CONTROLS",
    "one_hint": "Choose one key. It will be saved immediately.",
    "two_hint": "Choose both keys from the same device. Hold them together to grapple.",
    "escape_hint": "Esc cancels key capture. The console key is reserved. Each key keeps its normal action when pressed alone.",
    "keyboard": "Keyboard / mouse", "gamepad": "Controller", "game_controls": "Game controls",
    "invalid_keys": "Not saved. Choose distinct keys from the same device. Escape and the console key are reserved.",
    "controls_saved": "Controls saved.", "controls_reset": "Default grapple controls restored.",
    "current_controls": "Current bindings",
    "controller_icons": "CONTROLLER ICONS", "PS5": "PLAYSTATION", "XSX": "XBOX",
    "game_controls_pending": "Game controls (available in a session)",
    "reserved_key": "Not saved: this key is reserved for the console or cancel. Previous controls kept.",
    "theme": "THEME:", "theme:EMBER": "EMBER", "theme:DARK": "DARK", "theme:LIGHT": "LIGHT", "theme:BL4": "BL4",
    "theme_later": "Theme saved. It will show the next time you open this menu.",
    "window_size": "WINDOW:", "window_size:LARGE": "LARGE", "window_size:FULL": "FULL SCREEN",
    "window_size:NORMAL": "NORMAL",
    "window_size_later": "Window size saved. It will show the next time you open this menu.",
    # The LOOK page's sentence when the grapple gun's look gave way to the classic one (look_choice.notice).
    "look_missing": "The grapple gun cannot show: its files are missing or no longer match this version of the game. "
                    "Your game is not affected and the grapple keeps the classic look. Install the grapple gun's "
                    "files, then restart the game.",
    "look_failed": "The grapple gun stopped after an error. Your game is not affected and the grapple keeps the "
                   "classic look until the game restarts. The reason is in unrealsdk.log.",
    "look_unknown_hunter": "This hunter does not have the grapple gun yet: the grapple keeps the classic look.",
}

# The words a choice's buttons write (panel_choices.label), by "<setting>:<value>": a value is the letter of the drawing
# Kevin chose it on (look_settings.py), and the same letter means another thing on another row.
CHOICES = {
    "look:GRAPPLE_GUN": "Grapple gun", "look:CLASSIC": "Classic",
    "rope_look:A": "Thread", "rope_look:B": "Core", "rope_look:C": "Glow",
    "rope_thickness:K": "Thin", "rope_thickness:L": "Medium", "rope_thickness:M": "Thick",
    "rope_light:1": "Low", "rope_light:2": "Medium", "rope_light:3": "High",
    "rope_movement:G": "Slight", "rope_movement:H": "Medium", "rope_movement:I": "Strong",
    "hook_size:A": "Small", "hook_size:B": "Medium", "hook_size:C": "Large",
    "holster:WITH": "With", "holster:WITHOUT": "Without",
    "glow_face:D": "Off", "glow_face:E": "Light", "glow_face:F": "Strong",
    "rope_colour:ORANGE": "Orange", "rope_colour:RED": "Red", "rope_colour:PURPLE": "Purple",
    "rope_colour:WHITE": "White", "rope_colour:BLUE": "Blue", "rope_colour:TURQUOISE": "Turquoise",
    "rope_colour:YELLOW": "Yellow", "rope_colour:GOLD": "Gold", "rope_colour:GREEN": "Green",
    "game_rope_colour:ORANGE": "Orange", "game_rope_colour:RED": "Red", "game_rope_colour:PURPLE": "Purple",
    "game_rope_colour:WHITE": "White", "game_rope_colour:BLUE": "Blue", "game_rope_colour:TURQUOISE": "Turquoise",
    "game_rope_colour:YELLOW": "Yellow", "game_rope_colour:GOLD": "Gold", "game_rope_colour:GREEN": "Green",
}
