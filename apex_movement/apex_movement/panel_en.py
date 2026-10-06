"""Movement page names; common window messages come from Grapple's approved menu."""

from .panel_common_en import TEXT as COMMON

TEXT = {
    **COMMON,
    "camera_refused": "The camera could not confirm this change. It was not saved.",
    "camera_timeout": "The camera did not respond. Previous settings were restored. Try again in a moment.",
    "undone_partial": "Settings restored, except the camera: another mod controls it.",
    "options": "OPTIONS", "options_desc_menu": "Menu language.", "languages": "LANGUAGES",
    # The sentence under the Options title on its camera and commands tabs (Kevin, 2026-10-06).
    "camera_tab_desc": "View, aiming, orbit camera and loot.",
    "commands_tab_desc": "Camera keys, on keyboard and controller.",
    "camera": "CAMERA", "camera_desc": "View, field of view and loot.",
    # Omni Sprint and Third Person & FOV spread the camera settings over four pages (Kevin, 2026-10-06).
    "camera_page": "View on foot, shoulder and field of view.",
    "aiming": "AIMING", "aiming_page": "Third-person aiming and zoom.",
    "orbit_camera": "ORBIT CAMERA", "orbit_camera_page": "Circles the character at the distance you choose.",
    "loot": "LOOT", "loot_page": "Pick up loot from farther away.",
    "third_person_needed": "Turn on third person in the CAMERA tab.",
    "change_key": "CHANGE", "press_key": "PRESS A KEY", "no_key": "NONE",
    "commands": "COMMANDS", "keyboard": "KEYBOARD / MOUSE", "controller": "CONTROLLER",
    "command_third_person": "THIRD PERSON", "command_third_person_desc": "Turn third person on or off.",
    "command_shoulder": "SWITCH SHOULDER", "command_shoulder_desc": "Move the camera to the other shoulder.",
    "command_orbit": "ORBIT CAMERA", "command_orbit_desc": "Turn the Orbit Camera on or off.",
    "command_zoom_in": "ORBIT CAMERA ZOOM IN", "command_zoom_in_desc": "One step per press, in the Orbit Camera.",
    "command_zoom_out": "ORBIT CAMERA ZOOM OUT", "command_zoom_out_desc": "One step per press, in the Orbit Camera.",
    "command_tools": "COMMAND OPTIONS", "command_tools_desc": "Controller icons and camera command defaults.",
    "commands_reset": "DEFAULT KEYS", "controller_icons": "CONTROLLER ICONS",
    "camera_draft_discarded": "Camera mod changed: unsaved camera settings were discarded.",
    "camera_elsewhere": "Another camera mod controls the camera. Use its menu to adjust it.",
    "framing_saved_unavailable": "Saved. Framing preview is unavailable here.",
    "framing_saved_partial": "Saved. Part of the framing preview is unavailable here; check the camera rows.",
    "camera_outdated": "Camera mods of different versions are loaded. Update Apex Movement, Omni Sprint and "
                       "Third Person & FOV, then restart the game.",
    "right": "RIGHT", "left": "LEFT",
    "language": "LANGUAGE", "menu_language": "MENU LANGUAGE", "language_name": "ENGLISH",
    "movement": "MOVEMENT", "auto_sprint": "AUTO SPRINT", "slides": "SLIDES",
    "axle_slide": "AXLE SLIDE", "dash": "DASH", "glide": "GLIDE",
    "air_crouch": "SLAM & LANDING SLIDE", "air_strafe": "AIR / TAP STRAFE",
    "heavier_fall": "HEAVIER FALL", "wall_climb": "WALL CLIMB",
}
