"""The grapple gun's pistol and holster on the hunter: built on them, each hung on its bone as it is, shown in its
view at its moment, destroyed.

Four pieces (look_assets.PIECES), by their role: the arms' pistol in the first-person left hand, drawn with the arms;
the body's pistol in the left hand; the pistol in its holster, and the holster, on the hips. Their hold lives in
their meshes, so they hang with no move and no turn (trial 5b, docs/apex_grapple/pistolet-grappin/enquetes/
2026-10-05-nos-pieces-en-jeu.md). The held pistols are the same for every hunter; the holster and the pistol in it
are fitted on each one's hips, and C4SH has none, his coat covering his hip (look_assets.HUNTERS; decisions.md,
14 October). Through the eyes only the arms' pistol may show; from behind, the holster with the pistol in it or in
the hand (conception-pistolet-et-gestes.md, « Ce que le joueur voit »). A piece is shown or hidden only when that
changes.
"""

from typing import Any

from . import look_assets, look_load, look_pieces, look_view

ARMS_PISTOL, BODY_PISTOL, HOLSTERED, HOLSTER = "pistol_arms", "pistol_body", "pistol_holstered", "holster"


def keys(hunter: str) -> dict[str, str]:
    """The pieces `hunter` wears (look_hunter.of), by role: the key of each in look_assets.PIECES."""
    worn = {ARMS_PISTOL: "pistol_arms", BODY_PISTOL: "pistol_body"}
    holster = look_assets.HUNTERS[hunter]
    if holster is not None:
        worn.update({HOLSTERED: holster["holstered"], HOLSTER: holster["holster"]})
    return worn


def wanted(hunter: str) -> list[tuple[str, str]]:
    """What `hunter`'s pieces need from the game, as look_load.fetch takes it."""
    found = [(look_load.MATERIAL, look_assets.MATERIAL)]
    for key in keys(hunter).values():
        found.append((look_load.MESH, look_assets.PIECES[key]["mesh"]))
        found += [(look_load.TEXTURE, image["texture"]) for image in look_assets.PIECES[key]["textures"]]
    return found


def shown(view: str, arms_pistol: bool, in_hand: bool, holster: bool) -> set[str]:
    """The pieces seen, by role: through the eyes, the arms' pistol while the arm holds it; from behind, the pistol in
    the hand during a shot, in its holster otherwise, the holster kept or not as the player chose."""
    if view == look_view.FIRST:
        return {ARMS_PISTOL} if arms_pistol else set()
    seen = {BODY_PISTOL} if in_hand else ({HOLSTERED} if holster else set())
    return seen | ({HOLSTER} if holster else set())


class Gun:
    def __init__(self, character: Any, arms: Any, objects: dict, hunter: str) -> None:
        """`arms`: the first-person arms' mesh; `hunter`: whose pieces (look_hunter.of)."""
        self.pieces: dict[str, Any] = {}
        self.seen: set[str] = set()
        for role, key in keys(hunter).items():
            piece = look_assets.PIECES[key]
            on_arms = piece["on"] == "arms"
            made = look_pieces.new_piece(character, objects[piece["mesh"]], arms if on_arms else None)
            self.pieces[role] = made
            look_pieces.dressed(made, key, objects[look_assets.MATERIAL], objects)
            look_pieces.hang(made, arms if on_arms else character.Mesh, piece["bone"])

    def show(self, wanted_seen: set[str]) -> None:
        """Shows the roles in `wanted_seen` among those built, hides the others."""
        for role, made in self.pieces.items():
            if (role in wanted_seen) != (role in self.seen):
                made.SetVisibility(role in wanted_seen, False)
        self.seen = set(wanted_seen) & set(self.pieces)

    def destroy(self) -> None:
        look_pieces.destroy(list(self.pieces.values()))
