"""The game's calls that put a hunter's body on Lemmy (docs/renforts/sondes/wear_parts.py, trials 154 to 159).

Why these (docs/renforts/enquetes/2026-10-20-essai-156-lemmy-sur-l-ossature-de-loveless.md): parts hung on Lemmy and
following his bones kept his proportions and a misshapen face, for he lacks most of a hunter's head bones (trial 155).
So his own mesh draws the hunter's upper body, on the hunter's skeleton, and the game gives it a new animation of the
same class, which moves it (trial 156, vérifié en jeu); the hunter's other parts follow that mesh, every bone of theirs
found. A mesh keeps the materials set over its slots when it changes model (trial 158): each slot is given its
model's own material back (trial 159, vérifié en jeu).

Each call is made only while its parameters keep the names written in CALLS (differing), as the trials did: a game
update that changes one leaves Lemmy as he is rather than calling with guessed parameters.
"""

from itertools import islice
from typing import Any, Callable

import unrealsdk

# The hunters' parts are of one of these two classes (hunter change, essai 16).
MODEL_CLASSES = ("SkeletalMesh", "GestaltSkeletalMesh")
# The phoenix's materials, put over Lilith's (hunters.GUESTS): instances of her own, in the game files.
MATERIAL_CLASSES = ("MaterialInstanceConstant",)
# SkeletalMeshAsset alone reads nothing in this game (hunter change, essai 22): the model is in one of these.
MODEL_FIELDS = ("SkeletalMeshAsset", "SkinnedAsset", "SkeletalMesh")
COMPONENT = "SkeletalMeshComponent"
LOADER = "AssetRegistryHelpers"
KEEP_RELATIVE = 0
MOVABLE = 2
RETURNED = 0x400
CALLS = {
    "/Script/Engine.Actor:AddComponentByClass": ("Class", "bManualAttachment", "RelativeTransform", "bDeferredFinish"),
    "/Script/Engine.Actor:FinishAddComponent": ("Component", "bManualAttachment", "RelativeTransform"),
    "/Script/Engine.SkeletalMeshComponent:SetSkeletalMeshAsset": ("NewMesh",),
    "/Script/Engine.SceneComponent:SetMobility": ("NewMobility",),
    "/Script/Engine.SceneComponent:K2_AttachToComponent": ("Parent", "SocketName", "LocationRule", "RotationRule",
                                                           "ScaleRule", "bWeldSimulatedBodies"),
    "/Script/Engine.SkinnedMeshComponent:SetLeaderPoseComponent": ("NewLeaderBoneComponent", "bForceUpdate",
                                                                   "bInFollowerShouldTickPose"),
    "/Script/Engine.PrimitiveComponent:SetMaterial": ("ElementIndex", "Material"),
    # Not used by the trials: hides him while he is dressed (dress.py, trial 190; the parameter's name as Unreal
    # declares it, non vérifié in this game until a run reads it).
    "/Script/Engine.Actor:SetActorHiddenInGame": ("bNewHidden",),
    # The engine module that holds it is AssetRegistry, not Engine: trial 154's first run refused on that.
    "/Script/AssetRegistry.AssetRegistryHelpers:GetAsset": ("InAssetData",)}

Say = Callable[[str], None]


def params(function: Any) -> tuple:
    return tuple(str(prop.Name) for prop in function._properties()
                 if not int(getattr(prop, "PropertyFlags", 0)) & RETURNED)


def differing() -> list[str]:
    """The calls whose parameters are not the ones expected; empty when all hold."""
    found = []
    for path, expected in CALLS.items():
        try:
            have = params(unrealsdk.find_object("Function", path))
        except Exception:
            have = None
        if have != expected:
            found.append(path.rsplit(":", 1)[-1])
    return found


def model_of(mesh: Any) -> Any:
    for field in MODEL_FIELDS:
        found = getattr(mesh, field, None)
        if found is not None:
            return found
    return None


def drawing(mesh: Any) -> str | None:
    """The full path of the model the mesh draws; None when it draws none."""
    model = model_of(mesh)
    return None if model is None else model._path_name()


def asset_data(class_name: str, path: str) -> Any:
    """The names the engine's loader reads: package, its folder, the asset, and the asset's class."""
    package, name = path.rsplit(".", 1)
    kind_package, kind = unrealsdk.find_class(class_name)._path_name().rsplit(".", 1)
    return unrealsdk.make_struct("AssetData", PackageName=package, PackagePath=package.rsplit("/", 1)[0],
                                 AssetName=name, AssetClassPath=unrealsdk.make_struct(
                                     "TopLevelAssetPath", PackageName=kind_package, AssetName=kind))


def _found(class_name: str, path: str) -> Any:
    try:
        return unrealsdk.find_object(class_name, path)
    except ValueError:
        return None


def load(path: str, classes: tuple = MODEL_CLASSES) -> Any:
    """A model (or, given MATERIAL_CLASSES, a material) by its path, loaded from the game's archives if nothing has
    loaded it yet; None if it cannot be. The loader's answer is not relied on: the model is found again by its path
    (heirloom, 2026-09-23)."""
    for class_name in classes:
        found = _found(class_name, path)
        if found is not None:
            return found
    for class_name in classes:
        try:
            unrealsdk.find_class(LOADER).ClassDefaultObject.GetAsset(asset_data(class_name, path))
        except Exception:
            continue
        found = _found(class_name, path)
        if found is not None:
            return found
    return None


def identity() -> Any:
    """No offset, no turn, the model's own size; written out, as the heirloom does: a structure made empty would hold a
    scale of zero (non vérifié) and draw nothing."""
    return unrealsdk.make_struct("Transform", Rotation=unrealsdk.make_struct("Quat", X=0.0, Y=0.0, Z=0.0, W=1.0),
                                 Translation=unrealsdk.make_struct("Vector", X=0.0, Y=0.0, Z=0.0),
                                 Scale3D=unrealsdk.make_struct("Vector", X=1.0, Y=1.0, Z=1.0))


def draw(mesh: Any, model: Any) -> None:
    """The mesh made to draw the model; his own mesh then moves on the model's skeleton (trial 156)."""
    mesh.SetSkeletalMeshAsset(model)


def wear(actor: Any, body: Any, model: Any, placed: Any) -> Any:
    """A component drawing the model, hung on the body and following its bones."""
    made = actor.AddComponentByClass(unrealsdk.find_class(COMPONENT), True, placed, True)
    made = made[0] if isinstance(made, tuple) else made
    made.SetSkeletalMeshAsset(model)
    made.SetMobility(MOVABLE)
    actor.FinishAddComponent(made, True, placed)
    made.K2_AttachToComponent(body, "None", KEEP_RELATIVE, KEEP_RELATIVE, KEEP_RELATIVE, False)
    made.SetLeaderPoseComponent(body, True, False)
    return made


def hide(actor: Any, hidden: bool) -> None:
    """The whole character hidden or shown, each part keeping its own visibility."""
    actor.SetActorHiddenInGame(hidden)


def repaint(mesh: Any, model: Any, limit: int) -> int:
    """Each of the model's slots, limit at most, given the model's own material over whatever the mesh had set there
    for its last model; how many."""
    given = list(islice(model.Materials, limit))
    for index, slot in enumerate(given):
        mesh.SetMaterial(index, slot.MaterialInterface)
    return len(given)


def overpaint(mesh: Any, model: Any, swaps: dict, limit: int) -> int:
    """Each of the model's slots, limit at most, whose own material is a key of swaps (its full path, lower case)
    given the material it maps to; how many."""
    count = 0
    for index, slot in enumerate(islice(model.Materials, limit)):
        own = slot.MaterialInterface
        put = None if own is None else swaps.get(own._path_name().lower())
        if put is not None:
            mesh.SetMaterial(index, put)
            count += 1
    return count
