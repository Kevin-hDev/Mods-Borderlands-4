"""Values shared by every camera client."""

from .generated_ads import PROTOCOL
MAX_CLIENTS = 8
MAX_PROTOCOL_NOTE_VALUE = (1 << 32) - 1
GAME_MENU_MAX_FOV = 110.0
FOV_MIN = 70.0
FOV_MAX = 150.0
FOV_DEFAULT = 110.0
# The speed gain may go past the slider's 150, never near 180, where a view angle stops making sense.
FOV_CEILING = 170.0
# The over-the-shoulder camera's side and height (cm), added to the game's own view (view_target_math.cpp). Kevin moved
# the reticle 46 px right and 4 px up from the hunter on a 2560 px screenshot (2026-10-08, 03 h 53): at FOV 110 and the
# normal distance (256 cm), that is 13.1 cm right and 1.1 cm up. It was 48.4 and 5.0 before.
THIRD_PERSON_RIGHT = 61.5
THIRD_PERSON_UP = 6.1
CAMERA_TRANSITION = "Default"
CAMERA_BLEND = -1.0
CAMERA_TELEPORT = False
FFYL_MODE = "FFYL"
GROUND_SLAM_EXIT_MODE = "GroundSlamExit"
ORBIT_MODE = "Orbit"
THIRD_PERSON_MODE = "ThirdPerson"
CLIMB_MODE = "ThirdPersonClimbing"
LADDER_MODE = "ladder"
SCRIPTED_CLIMB_NONE = 0
SCRIPTED_CLIMB_MAX = 255
