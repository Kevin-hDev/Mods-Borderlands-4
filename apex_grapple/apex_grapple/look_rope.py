"""One rope of the grapple gun's look: its pieces built on the character and dressed, laid along the rope's curve at
each frame, shown or hidden, destroyed.

Each look is drawn as pieces of a whole number of turns of its twist, worn end to end: each piece is stretched from one
place on the curve to the next (rope_motion.laid), so the twist keeps one pitch without a seam (verified in game on
2026-10-07, and hanging on 2026-10-13: docs/apex_grapple/pistolet-grappin/enquetes/2026-10-13-corde-qui-bouge-en-
jeu.md). Every piece shown is put in the world at every frame, about 0.06 ms each, twice that with C's glow (measured
up to 40 m). C's glow goes along C as pieces of its own, in the game's additive effect material, put where C's are
(verified in game, trial 7).

The light takes the player's colour (docs/apex_grapple/pistolet-grappin/decisions.md, 14 October): the glow's mask
is painted orange, its light on the red channel, which is given the chosen colour over the painted red; C's glow is
painted in its image, one per colour, the chosen one put in its material when the rope is built.
"""

import math
from typing import Any

import unrealsdk

from . import look_assets, look_load, look_pieces, rope_motion

# A quarter more pieces than the range holds: the rope's bow, and a player running away while the hook flies or comes
# back. Past that, the pieces stretch rather than the rope stopping short of the hook.
SPARE = 1.25
_ROPE, _PIECES = look_assets.ROPE, look_assets.PIECES
# The mask's channel that carries the light: the painted orange is mostly red, its other channels go dark.
LIT_CHANNEL = "Emissive Color (Red Channel)"
DARK = (0.0, 0.0, 0.0, 1.0)


def _keys(look: str) -> list[tuple[str, str]]:
    """The look's pieces, each with the material it wears: the rope's, then its glow's when it has one."""
    keys = [(_ROPE["pieces"][look], look_assets.MATERIAL)]
    if look in _ROPE["halo"]["looks"]:
        keys.append((_ROPE["halo"]["piece"], _ROPE["halo"]["material"]))
    return keys


def glows(look: str) -> bool:
    return look in _ROPE["halo"]["looks"]


def wanted(look: str, colour: str) -> list[tuple[str, str]]:
    """What a rope of `look` in `colour` needs from the game, as look_load.fetch takes it."""
    needs = []
    for key, material in _keys(look):
        needs += [(look_load.MESH, _PIECES[key]["mesh"]), (look_load.MATERIAL, material)]
        needs += [(look_load.TEXTURE, image["texture"]) for image in _PIECES[key]["textures"]]
    if glows(look):
        needs.append((look_load.TEXTURE, _ROPE["halo"]["images"][colour]))
    return needs


def _length(key: str) -> float:
    low, high = _PIECES[key]["box_cm"]
    return high[2] - low[2]


def piece_cm(look: str, thickness: str) -> float:
    """How long one piece of `look` is worn at `thickness`, unstretched: drawn 1 cm across, scaled to the thickness."""
    return _length(_ROPE["pieces"][look]) * _ROPE["thicknesses_cm"][thickness] / _ROPE["across_cm"]


def count(look: str, thickness: str, range_cm: float) -> int:
    return math.ceil(range_cm * SPARE / piece_cm(look, thickness))


def z_toward(start: tuple, end: tuple) -> tuple[float, float]:
    """Pitch and yaw that turn a model's +Z from start toward end, roll 0, in Unreal's order (corde_pose.py, verified
    in game)."""
    east, north, up = (b - a for a, b in zip(start, end))
    return math.degrees(math.atan2(-math.hypot(east, north), up)) + 0.0, math.degrees(math.atan2(north, east)) + 0.0


def _setting(entry: dict) -> Any:
    return unrealsdk.make_struct("MaterialParameterInfo", Name=entry["name"], Association=entry["association"],
                                 Index=entry["index"])


class Rope:
    """`count` pieces of `look`, and as many of its glow in `colour`, built hidden on `character` from `objects`
    (look_load)."""

    def __init__(self, character: Any, look: str, thickness: str, count: int, objects: dict, colour: str) -> None:
        self.look, self.thickness, self.count = look, thickness, count
        self.strands: list[tuple[list[Any], float]] = []
        self.material: Any = None
        self.shown = 0
        for key, parent in _keys(look):
            mesh = objects[_PIECES[key]["mesh"]]
            first = look_pieces.new_piece(character, mesh)
            slot, material = look_pieces.dressed(first, key, objects[parent], objects)
            if key == _ROPE["halo"]["piece"]:
                image = _PIECES[key]["textures"][0]
                material.SetTextureParameterValueByInfo(_setting(
                    {"name": image["parameter"], "association": image["association"], "index": image["layer"]}),
                    objects[_ROPE["halo"]["images"][colour]])
            pieces = [first]
            for _ in range(1, count):
                made = look_pieces.new_piece(character, mesh)
                made.SetMaterial(slot, material)
                pieces.append(made)
            self.strands.append((pieces, _length(key)))
            if self.material is None:
                self.material = material

    def light(self, strength: float, colour: str, face: str) -> None:
        """The rope's light at `strength` in `colour`; for a look that wears a glow, its face at the share `face` of
        that strength."""
        if glows(self.look):
            strength *= look_assets.ROPE_FACES[face]
        for entry in _ROPE["scalars"]:
            self.material.SetScalarParameterValueByInfo(_setting(entry), strength)
        painted = look_assets.GLOW_PAINTED[0]
        lit = (*(part / painted for part in look_assets.COLOURS[colour]), 1.0)
        for entry in _ROPE["vectors"]:
            red, green, blue, alpha = lit if entry["name"] == LIT_CHANNEL else DARK
            self.material.SetVectorParameterValueByInfo(_setting(entry), unrealsdk.make_struct(
                "LinearColor", R=red, G=green, B=blue, A=alpha))

    def lay(self, points: list[tuple]) -> int:
        """Every piece along the curve through `points`, the others hidden; returns how many show."""
        total = sum(math.dist(a, b) for a, b in zip(points, points[1:]))
        places = rope_motion.laid(points, max(piece_cm(self.look, self.thickness), total / self.count))
        thin = _ROPE["thicknesses_cm"][self.thickness] / _ROPE["across_cm"]
        turns = [z_toward(start, end) for start, end in places]
        for pieces, model_length in self.strands:
            for made, (start, end), (pitch, yaw) in zip(pieces, places, turns):
                look_pieces.put(made, start, pitch, yaw, (thin, thin, math.dist(start, end) / model_length))
        self.show(len(places))
        return len(places)

    def show(self, wanted: int) -> None:
        """The first `wanted` pieces of each strand shown, the others hidden, calling the game only for those that
        change."""
        for pieces, _ in self.strands:
            for number in range(min(self.shown, wanted), max(self.shown, wanted)):
                pieces[number].SetVisibility(number < wanted, False)
        self.shown = wanted

    def destroy(self) -> None:
        pieces = [made for strand, _ in self.strands for made in strand]
        self.strands = []
        look_pieces.destroy(pieces)
