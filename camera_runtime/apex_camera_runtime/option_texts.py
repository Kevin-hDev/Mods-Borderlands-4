"""The camera options' English names and descriptions, shared by the three mods that own the camera.

One source: they were copied by hand into each mod's settings, and a wording changed in one copy survived in the
others (review, 2026-09-26). The French texts are Apex Movement's panel_fr.py, generated into the two others.
"""

THIRD_PERSON = {"display_name": "Third Person", "description": "Keep the on-foot camera behind the character."}
# The SDK's text menu reads On/Off for a switch; the shoulder's two values are sides (review, 2026-09-26).
SHOULDER = {"display_name": "Shoulder", "description": "Put the camera over the left or right shoulder.",
            "true_text": "Left", "false_text": "Right"}
ORBIT = {"display_name": "Orbit Camera", "description": "The camera turns freely around the character."}
# Apex Movement and Omni Sprint only: Third Person & FOV always applies its FOV.
CUSTOM_FOV = {"display_name": "Custom FOV", "description": "Use the FOV below instead of the game's."}
FOV ={"display_name": "FOV", "description": "Field of view, up to 150."}
