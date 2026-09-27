"""Movement page names; common window messages come from Grapple's approved menu."""

from .panel_common_en import TEXT as COMMON

TEXT = {
    **COMMON,
    "options": "OPTIONS", "options_desc": "Camera and menu language.", "options_desc_menu": "Menu language.",
    "camera": "CAMERA", "camera_desc": "View, field of view and loot.",
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
    "right": "RIGHT", "left": "LEFT",
    "language": "LANGUAGE", "menu_language": "MENU LANGUAGE", "language_name": "ENGLISH",
    "movement": "MOVEMENT", "auto_sprint": "AUTO SPRINT", "slides": "SLIDES",
    "axle_slide": "AXLE SLIDE", "dash": "DASH", "glide": "GLIDE",
    "air_crouch": "SLAM & LANDING SLIDE", "air_strafe": "AIR / TAP STRAFE",
    "heavier_fall": "HEAVIER FALL", "wall_climb": "WALL CLIMB",
}
