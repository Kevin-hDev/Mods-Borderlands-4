"""Movement page names; common window messages come from Grapple's approved menu."""

from .panel_common_en import TEXT as COMMON

TEXT = {
    **COMMON,
    "camera_refused": "The camera could not confirm this change. It was not saved.",
    "camera_timeout": "The camera did not respond. Previous settings were restored. Try again in a moment.",
    "undone_partial": "Settings restored, except the camera: another mod controls it.",
    "options": "OPTIONS", "options_desc_menu": "Menu language.", "languages": "LANGUAGES",
    # The sentence under the Options title on its camera and commands tabs (Kevin, 2026-10-06).
    "camera_tab_desc": "View, orbit camera and loot.",
    "commands_tab_desc": "Camera keys, on keyboard and controller.",
    "camera": "CAMERA", "camera_desc": "View, field of view and loot.",
    # The camera tab's two halves (Kevin, 2026-10-07).
    "camera_view": "CAMERA VIEW", "shoulder_view": "SHOULDER VIEW", "shoulder": "SHOULDER VIEW",
    "shoulder_tab_desc": "Camera shoulder and automatic switch.",
    "shoulder_desc": "Pick the shoulder, and let the camera switch shoulders in front of a wall.",
    # Omni Sprint and Third Person & FOV spread the camera settings over four pages (Kevin, 2026-10-06).
    "camera_page": "View on foot, field of view and Free Look.",
    "aiming": "AIMING", "aiming_page": "Third-person aiming and zoom.", "aiming_tab_desc": "Aim view and aim zoom.",
    "sensitivity": "SENSITIVITY", "sensitivity_tab_desc": "Camera speed in third person.",
    "sensitivity_page": "In percent of the game's own sensitivity: 100 changes nothing.",
    "orbit_camera": "ORBIT CAMERA", "orbit_camera_page": "Circles the character at the distance you choose.",
    "loot": "LOOT", "loot_page": "Pick up loot from farther away.",
    # The DYNAMIC CAMERA page, its three cards the same in the three camera mods (Kevin, 2026-10-06).
    "dynamic_camera": "DYNAMIC CAMERA", "dynamic_camera_tab_desc": "Field of view, framing and motion.",
    "dynamic_camera_page": "The camera follows the action: speed, jumps, crouching and driving.",
    "dynamic_fov": "FIELD OF VIEW", "dynamic_fov_desc": "Wider while sprinting or sliding.",
    "dynamic_framing": "FRAMING",
    "dynamic_framing_desc": "Back when running, jumping or driving fast, closer when crouched.",
    "dynamic_motion": "MOTION", "dynamic_motion_desc": "Soft inertia, and a faint drift when standing still.",
    "third_person_needed": "Turn on third person in the CAMERA tab.",
    "change_key": "CHANGE", "press_key": "PRESS A KEY", "no_key": "NONE",
    "commands": "COMMANDS", "keyboard": "KEYBOARD / MOUSE", "controller": "CONTROLLER",
    "command_third_person": "THIRD PERSON", "command_third_person_desc": "Turn third person on or off.",
    "command_shoulder": "SWITCH SHOULDER", "command_shoulder_desc": "Move the camera to the other shoulder.",
    "command_orbit": "ORBIT CAMERA", "command_orbit_desc": "Turn the Orbit Camera on or off.",
    "command_zoom_in": "ORBIT CAMERA ZOOM IN", "command_zoom_in_desc": "One step per press, in the Orbit Camera.",
    "command_zoom_out": "ORBIT CAMERA ZOOM OUT", "command_zoom_out_desc": "One step per press, in the Orbit Camera.",
    "command_free_look": "FREE LOOK", "command_free_look_desc": "Hold to turn the camera while you keep your direction.",
    "command_camera_distance": "CAMERA DISTANCE", "command_camera_distance_desc": "Close, normal or far, in third person.",
    "command_sniper_zoom": "OPTIC ZOOM",
    "command_sniper_zoom_desc": "While aiming with several zooms ticked, switch to the next one.",
    "popup_optics": "OPTICS", "popup_optics_desc": "Each weapon type's zoom in third person.",
    "optics_help_text": "BDL4: the weapon aims as in the game, in first person.\n\n"
                        "x1: the weapon aims at the shoulder with a light zoom.\n\n"
                        "x2 and up: the weapon aims at the shoulder with that zoom.\n\n"
                        "Several zooms ticked: while aiming, the zoom key goes to the next one, smallest to largest, "
                        "then back to the first. The next aim with that weapon type starts on the last zoom used.",
    "optics_help_key": "ZOOM KEY", "optics_help_commands": "Change it on the COMMANDS page.",
    "omni_direction": "OMNI DIRECTION", "omni_direction_tab_desc": "The body follows your run, in third person.",
    "omni_direction_page": "The body follows your run, in third person.",
    "omni_full_turn": "360°", "omni_half_turn": "180°", "omni_dash": "DASH", "omni_slide": "SLIDE",
    "popup_omni_body": "BODY ORIENTATION", "popup_omni_body_desc": "The hunter turns toward the run.",
    "omni_body_help_text": "In third person, the hunter turns toward the direction of the run instead of keeping "
                           "their back to the camera.\n\n"
                           "The hunter turns back to the crosshair to shoot, throw a grenade, melee or use the skill, "
                           "and goes back to the run a second after the last action.\n\n"
                           "While aiming, the hunter faces the crosshair. During a slide, the body keeps facing the "
                           "slide.",
    "popup_omni_angle": "ANGLE", "popup_omni_angle_desc": "How far the body turns.",
    "omni_angle_help_text": "360°: the hunter turns toward the run on every side. Backward, the hunter runs facing "
                            "the camera.\n\n"
                            "180°: the hunter turns on the sides and forward. Backward, the hunter backs up with "
                            "their back to the camera, as in the game.",
    "popup_omni_crouch": "SIDES AND BACK", "popup_omni_crouch_desc": "Crouching while sprinting sideways or backward.",
    "omni_crouch_help_text": "When you sprint sideways or backward, crouching starts:\n\n"
                             "DASH: the dash, as when you run without sprinting.\n\n"
                             "SLIDE: a slide, as when sprinting forward.\n\n"
                             "Forward, crouching always slides.",
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
