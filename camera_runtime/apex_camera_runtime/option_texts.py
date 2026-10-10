"""The camera options' English names and descriptions, shared by the three mods that own the camera.

One source: they were copied by hand into each mod's settings, and a wording changed in one copy survived in the
others (review, 2026-09-26). The French texts are Apex Movement's panel_fr.py, generated into the two others.
"""

from .ads_optic import ZOOMS

THIRD_PERSON = {"display_name": "Third Person", "description": "Keep the on-foot camera behind the character."}
# The AIMING page's rows of boxes (weapon_optic_options.py).
_OPTIC = "BDL4 restores the game's first-person aim; zooms aim at the shoulder."
WEAPON_OPTICS = {
    "pistol_optics": {"display_name": "Pistol optic", "description": _OPTIC},
    "smg_optics": {"display_name": "SMG optic", "description": _OPTIC},
    "shotgun_optics": {"display_name": "Shotgun optic", "description": _OPTIC},
    "assault_optics": {"display_name": "Assault rifle optic", "description": _OPTIC},
    "sniper_optics": {"display_name": "Sniper optic", "description": _OPTIC},
    "heavy_optics": {"display_name": "Heavy weapon optic", "description": _OPTIC},
}
AIM_VIEW = {"display_name": "Aim View", "true_text": "Third Person", "false_text": "First Person",
            "description": "Each weapon type's optic is chosen below."}
# The SDK's text menu reads On/Off for a switch; the shoulder's two values are sides (review, 2026-09-26).
SHOULDER_SMOOTH = {"display_name": "Smooth shoulder switch", "description": "Animate camera movement when switching shoulders."}
ORBIT_SMOOTH = {"display_name": "Smooth camera transitions",
                "description": "Smooth the added offset for first/third-person and Orbit transitions."}
SHOULDER_SECONDS = {"display_name": "Transition animation",
                    "description": "Shared shoulder and camera-mode offset duration in seconds."}
# "Shoulder switch", Kevin's name (2026-10-07): "Shoulder" alone said nothing.
SHOULDER = {"display_name": "Shoulder switch", "description": "Put the camera over the left or right shoulder.",
            "true_text": "Left", "false_text": "Right"}
SHOULDER_AUTO = {"display_name": "Automatic shoulder switch",
                 "description": "Move the camera to the other shoulder when a wall blocks the view, then back."}
SHOULDER_AUTO_SWAP = {"display_name": "Automatic shoulder: switch delay",
                      "description": "How long a wall blocks the view before the camera switches, in seconds."}
SHOULDER_AUTO_RETURN = {"display_name": "Automatic shoulder: return delay",
                        "description": "How long the view stays clear before the camera comes back, in seconds."}
ORBIT = {"display_name": "Orbit Camera", "description": "The camera turns freely around the character."}
# Shown on the ORBIT CAMERA page of Omni Sprint and Third Person & FOV (Kevin, 2026-10-06), hidden from the SDK menu.
ORBIT_DISTANCE = {"display_name": "Distance", "description": "Camera distance, also set by the zoom keys."}
# Hidden from the SDK menu: the Camera Distance key chooses it (camera_distance.py).
CAMERA_DISTANCE = {"display_name": "Camera distance", "description": "Close, normal or far, chosen with its key."}
CAMERA_DISTANCE_CLOSE = {"display_name": "Camera distance: close",
                         "description": "How far behind you the close camera sits, in metres. Normal is 2.56."}
CAMERA_DISTANCE_FAR = {"display_name": "Camera distance: far",
                       "description": "How far behind you the far camera sits, in metres. Normal is 2.56."}
# The SENSITIVITY page (look_sensitivity_options.py): percent of the game's own sensitivity, mouse and controller,
# third person only.
SENSITIVITY_LOOK = {"display_name": "Third-person look sensitivity",
                    "description": "Camera turn speed in third person, mouse and controller, in percent of the game's."}
SENSITIVITY_AIM = {"display_name": "Third-person aim sensitivity",
                   "description": "Camera turn speed while aiming over the shoulder, mouse and controller, "
                                  "in percent of the game's."}
SENSITIVITY_WEAPONS = {"display_name": "Sensitivity per weapon type",
                       "description": "While aiming in third person, each weapon type uses its own value below."}
SENSITIVITY_PER_OPTIC = {"display_name": "Per optic zoom",
                         "description": "Each zoom uses its own value below, with every weapon."}
SENSITIVITY_WEAPON = {
    "pistol": {"display_name": "Pistols", "description": "Aim speed with a pistol, in percent of the game's."},
    "smg": {"display_name": "SMGs", "description": "Aim speed with an SMG, in percent of the game's."},
    "shotgun": {"display_name": "Shotguns", "description": "Aim speed with a shotgun, in percent of the game's."},
    "assault": {"display_name": "Assault rifles",
                "description": "Aim speed with an assault rifle, in percent of the game's."},
    "sniper": {"display_name": "Sniper rifles",
               "description": "Aim speed with a sniper rifle, in percent of the game's."},
    "heavy": {"display_name": "Heavy weapons",
              "description": "Aim speed with a heavy weapon, in percent of the game's."},
    # Named for the sniper rifle, the first weapon with optics: the names keep the players' saved values.
    **{f"sniper_x{zoom}": {"display_name": f"Optic x{zoom}",
                           "description": f"Aim speed with the x{zoom} zoom, in percent of the game's."}
       for zoom in ZOOMS},
}
# Apex Movement and Omni Sprint only: Third Person & FOV always applies its FOV.
CUSTOM_FOV = {"display_name": "Custom FOV", "description": "Use the FOV below instead of the game's."}
FOV ={"display_name": "FOV", "description": "Field of view, up to 150."}
SPEED_FOV = {"display_name": "Speed FOV", "description": "Widen the view while sprinting."}
SPEED_FOV_GAIN = {"display_name": "Speed FOV gain", "description": "Field of view added while sprinting."}
SPEED_FOV_SECONDS = {"display_name": "Speed FOV transition", "description": "Seconds to widen and to come back."}
ACTION_FRAMING = {"display_name": "Action framing",
                  "description": "Moves the camera back while running, in the air or driving fast, and closer when "
                                 "crouched."}
ACTION_FRAMING_STRENGTH = {"display_name": "Action framing strength",
                           "description": "100% is the default; lower is softer, higher stronger."}
CAMERA_MOTION = {"display_name": "Camera motion",
                 "description": "The camera follows your changes of speed softly, and drifts a little when you stand still."}
CAMERA_MOTION_STRENGTH = {"display_name": "Camera motion strength",
                          "description": "100% is the default; lower is softer, higher stronger."}
# Shown on the CAMERA page (free_look_options.py).
FREE_LOOK = {"display_name": "Free Look", "description": "Hold its key to turn the camera while you keep your direction."}
FREE_LOOK_KEYBOARD_HOLD = {"display_name": "Keyboard: Hold for Free Look",
                           "description": "On: Free Look lasts while the key is held. Off: each press turns it on or off."}
FREE_LOOK_CONTROLLER_HOLD = {"display_name": "Controller: Hold for Free Look",
                             "description": "On: Free Look lasts while the button is held. Off: each press turns it on "
                                            "or off."}
FREE_LOOK_HOLD_TIME = {"display_name": "Free Look hold time",
                       "description": "How long to hold before Free Look starts, in seconds."}
# The OMNI DIRECTION page (omni_direction_options.py, Kevin 2026-10-09).
OMNI_BODY = {"display_name": "Body Orientation", "description": "The hunter turns toward the direction of the run."}
OMNI_ANGLE = {"display_name": "Angle",
              "description": "360: on every side. 180: backward, the hunter backs up as in the game."}
OMNI_SPRINT = {"display_name": "Sprint in All Directions", "description": "Also sprint sideways and backward."}
OMNI_CROUCH = {"display_name": "Sides and Back",
               "description": "Sprinting sideways or backward, crouching dashes or slides."}

ADS_NOTICES = {
    "unsupported": "Shoulder aiming is unavailable on this version. Keep first-person aiming until the mod is updated.",
    "unknown_weapon": "Weapon not recognized: first-person aiming retained. Try another weapon.",
    "heavy_native": "Heavy weapons keep first-person aiming.",
    "wrong_thread": "Aim presentation is unavailable: first-person aiming retained. Report this issue with the log.",
    "mode_unavailable": "Aim view not confirmed: first-person aiming retained. Release and aim again.",
    "cleanup_pending": "Returning to the game view. Wait before changing camera mods.",
    "install_failed": "Shoulder aiming could not start. Restart the game; if this persists, report it with the log.",
}
