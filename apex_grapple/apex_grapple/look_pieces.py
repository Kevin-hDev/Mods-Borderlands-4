"""One of our pieces made in the game: a mesh added to the character by hand, left unattached so that it stays where it
is put, and dressed in a material of the game with our images. The calls are those the trials made in game
(docs/apex_grapple/pistolet-grappin/sondes/pieces_essai.py, corde_construction.py; verified on 2026-10-05 and -07).
"""

from typing import Any

import unrealsdk

from . import look_assets, rope_ends

COMPONENT = "StaticMeshComponent"
# EComponentMobility 2, Movable: the only one that may move after it is built.
MOVABLE = 2
NO_SLOT = -1
# What decides how and where the first-person arms are drawn, copied onto a piece they hold so that it is drawn with
# them (Apex Heirloom's apex_held_object.py, 2026-09-23 and -26; our arms' pistol in trial 5b, 2026-10-05).
DRAW_FLAGS = ("bGbxForeground", "FirstPersonPrimitiveType", "DepthPriorityGroup", "bUseViewOwnerDepthPriorityGroup",
              "ViewOwnerDepthPriorityGroup", "bOnlyOwnerSee", "bOwnerNoSee", "CastShadow", "bReceivesDecals")
# EAttachmentRule 0: the transform given at creation stays the one relative to the bone.
KEEP_RELATIVE = 0

# Each dressed piece gets a material of its own name: the engine names the instances it makes.
_made = 0


def held() -> Any:
    """No move, no turn, full size: what a new piece takes; a bare Transform would scale it to nothing."""
    return unrealsdk.make_struct("Transform", Rotation=unrealsdk.make_struct("Quat", X=0.0, Y=0.0, Z=0.0, W=1.0),
                                 Translation=rope_ends.vector((0.0, 0.0, 0.0)),
                                 Scale3D=rope_ends.vector((1.0, 1.0, 1.0)))


def new_piece(character: Any, mesh: Any, drawn_as: Any = None) -> Any:
    """`mesh` added to the character, hidden; drawn as `drawn_as` is, when given (the first-person arms), its flags
    copied before the piece is finished, as the trials did."""
    made = character.AddComponentByClass(unrealsdk.find_class(COMPONENT), True, held(), True)
    if isinstance(made, tuple):
        made = made[0] if made else None
    if made is None:
        raise RuntimeError("the character handed back no component")
    made.SetStaticMesh(mesh)
    made.SetMobility(MOVABLE)
    if drawn_as is not None:
        for flag in DRAW_FLAGS:
            setattr(made, flag, getattr(drawn_as, flag))
    character.FinishAddComponent(made, True, held())
    made.SetVisibility(False, False)
    return made


def hang(made: Any, parent: Any, bone: str) -> None:
    """The piece on `bone` of `parent`, with no move and no turn: its hold lives in its mesh (trial 5b)."""
    made.K2_AttachToComponent(parent, bone, KEEP_RELATIVE, KEEP_RELATIVE, KEEP_RELATIVE, False)


def dressed(made: Any, key: str, parent: Any, objects: dict) -> tuple[int, Any]:
    """The piece's slot in a new instance of `parent`, the images of our piece `key` in it, taken from `objects`
    (look_load.fetch); returns the slot and the instance."""
    global _made
    slot = made.GetMaterialIndex(look_assets.SLOT)
    if slot == NO_SLOT:
        raise RuntimeError(f"our piece {key} has no {look_assets.SLOT} slot")
    _made += 1
    material = made.CreateDynamicMaterialInstance(slot, parent, f"MID_ApexGrapple_{key}_{_made}")
    for image in look_assets.PIECES[key]["textures"]:
        material.SetTextureParameterValueByInfo(unrealsdk.make_struct(
            "MaterialParameterInfo", Name=image["parameter"], Association=image["association"], Index=image["layer"]),
            objects[image["texture"]])
    return slot, material


def put(made: Any, start: tuple, pitch: float, yaw: float, scale: tuple) -> None:
    made.K2_SetWorldLocationAndRotation(
        rope_ends.vector(start), unrealsdk.make_struct("Rotator", Pitch=pitch, Yaw=yaw, Roll=0.0),
        False, unrealsdk.make_struct("HitResult"), True)
    made.SetWorldScale3D(rope_ends.vector(scale))


def destroy(pieces: list[Any]) -> None:
    """Every piece removed; each one tried even when another fails, the first failure raised after."""
    failed = None
    for made in pieces:
        try:
            made.K2_DestroyComponent(made.GetOwner())
        except Exception as error:
            failed = failed or error
    if failed is not None:
        raise failed
