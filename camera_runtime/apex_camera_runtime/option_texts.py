"""The camera options' English names and descriptions, shared by the three mods that own the camera.

One source: they were copied by hand into each mod's settings, and a wording changed in one copy survived in the
others (review, 2026-09-26). The French texts are Apex Movement's panel_fr.py, generated into the two others.
"""

THIRD_PERSON = {"display_name": "Third Person", "description": "Keep the on-foot camera behind the character."}
AIM_VIEW = {"display_name": "Aim View", "true_text": "Third Person", "false_text": "First Person",
            "description": "Sniper rifles and heavy weapons use first-person aiming."}
# The SDK's text menu reads On/Off for a switch; the shoulder's two values are sides (review, 2026-09-26).
SHOULDER_SMOOTH = {"display_name": "Smooth shoulder switch", "description": "Animate camera movement when switching shoulders."}
ORBIT_SMOOTH = {"display_name": "Smooth camera transitions",
                "description": "Smooth the added offset for first/third-person and Orbit transitions."}
SHOULDER_SECONDS = {"display_name": "Transition animation",
                    "description": "Shared shoulder and camera-mode offset duration in seconds."}
SHOULDER = {"display_name": "Shoulder", "description": "Put the camera over the left or right shoulder.",
            "true_text": "Left", "false_text": "Right"}
ORBIT = {"display_name": "Orbit Camera", "description": "The camera turns freely around the character."}
# Shown on the ORBIT CAMERA page of Omni Sprint and Third Person & FOV (Kevin, 2026-10-06), hidden from the SDK menu.
ORBIT_DISTANCE = {"display_name": "Distance", "description": "Camera distance, also set by the zoom keys."}
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

ADS_NOTICES = {
    "unsupported": "Shoulder aiming is unavailable on this version. Keep first-person aiming until the mod is updated.",
    "unknown_weapon": "Weapon not recognized: first-person aiming retained. Try another weapon.",
    "heavy_native": "Heavy weapons keep first-person aiming.",
    "wrong_thread": "Aim presentation is unavailable: first-person aiming retained. Report this issue with the log.",
    "mode_unavailable": "Aim view not confirmed: first-person aiming retained. Release and aim again.",
    "cleanup_pending": "Returning to the game view. Wait before changing camera mods.",
    "install_failed": "Shoulder aiming could not start. Restart the game; if this persists, report it with the log.",
}
