"""The grapple gun's hook: built on the character and dressed, put at the end of its rope at the player's size, hidden,
destroyed.

Its mesh's origin is its base hole and its point the far end of its box along +X, as the build makes it
(docs/apex_grapple/pistolet-grappin/fabrique/blender_pieces.py). Seen planted in game (trial 5b, 2026-10-05); flying
out and coming back, it is new. Its three sizes are Kevin's (decisions.md of that dossier, 5 October).
"""

import math
from typing import Any

from . import look_assets, look_load, look_pieces

KEY = "hook"
_PIECE = look_assets.PIECES[KEY]


def wanted() -> list[tuple[str, str]]:
    """What the hook needs from the game, as look_load.fetch takes it."""
    return [(look_load.MESH, _PIECE["mesh"]), (look_load.MATERIAL, look_assets.MATERIAL),
            *((look_load.TEXTURE, image["texture"]) for image in _PIECE["textures"])]


def length(size: str) -> float:
    """From its base hole to its point, in cm, at `size`."""
    return _PIECE["box_cm"][1][0] * look_assets.HOOK_SIZES[size]


def facing(way: tuple) -> tuple[float, float]:
    """Pitch and yaw that turn the hook's +X along `way`, roll 0."""
    east, north, up = way
    return math.degrees(math.atan2(up, math.hypot(east, north))) + 0.0, math.degrees(math.atan2(north, east)) + 0.0


class Hook:
    def __init__(self, character: Any, objects: dict) -> None:
        self.made = look_pieces.new_piece(character, objects[_PIECE["mesh"]])
        look_pieces.dressed(self.made, KEY, objects[look_assets.MATERIAL], objects)
        self.visible = False

    def put(self, base: tuple, way: tuple, size: str) -> None:
        """Its base hole on `base`, its point along `way`, shown."""
        scale = look_assets.HOOK_SIZES[size]
        look_pieces.put(self.made, base, *facing(way), (scale, scale, scale))
        if not self.visible:
            self.made.SetVisibility(True, False)
            self.visible = True

    def hide(self) -> None:
        if self.visible:
            self.made.SetVisibility(False, False)
            self.visible = False

    def destroy(self) -> None:
        look_pieces.destroy([self.made])
