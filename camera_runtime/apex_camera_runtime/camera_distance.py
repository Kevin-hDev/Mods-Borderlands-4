"""The camera's distance on foot in third person, chosen with one key: close, normal or far (Kevin, 2026-10-07, idea 2,
as GTA V does).

Game units (centimetres) behind the hunter. Normal is the game's own (ThirdPerson: 256 back,
Nexus-Data-camera_mode0.json), so a player who never presses the key keeps the game's camera; close and far are set on
the CAMERA VIEW page (camera_distance_options.py). The game checks walls after our offset (verified in game,
2026-09-26), so a far camera still comes in against a wall.
"""

CLOSE, NORMAL, FAR = 0, 1, 2
NORMAL_CM = 256.0
# Kevin's trial values (« ça fonctionne très bien c'est nickel ! », 2026-10-07): the defaults of the two settings.
DISTANCES = (180.0, NORMAL_CM, 360.0)
NAMES = ("close", "normal", "far")
SECONDS = 0.25


def valid(index: object) -> bool:
    return type(index) is int and 0 <= index < len(DISTANCES)


def following(index: object) -> int:
    """Close, normal, far, then close again; a hand-edited value starts over from normal."""
    return (index + 1) % len(DISTANCES) if valid(index) else NORMAL


def offset(index: object, distances: tuple = DISTANCES) -> float:
    """What the camera offset adds forward (X): positive brings the camera closer."""
    return NORMAL_CM - distances[index if valid(index) else NORMAL]
