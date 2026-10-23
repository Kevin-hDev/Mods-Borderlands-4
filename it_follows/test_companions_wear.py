"""Tests the calls that put a hunter's body on Lemmy (companions/wear.py, from docs/renforts/sondes/wear_parts.py): a
call's parameters without its return value; the calls whose parameters differ, or are missing, listed; the model a
mesh draws, read as the game holds it, by its full path; the loader's names; a part found loaded, or loaded then found
again by its path, under either class, or None; a mesh given a model; a part hung in order: made deferred, its model,
free to move, finished, attached, following the body; the placement written out with no offset and the model's own
size; each of a model's slots given its own material back, in order, bounded; the whole character hidden or shown
by its own flag."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows.companions import hunters, wear  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def ns(**fields: object) -> types.SimpleNamespace:
    return types.SimpleNamespace(**fields)


def find_object(kind: str, path: str) -> object:
    """The game's: a path not found raises ValueError."""
    try:
        return state["objects"][(kind, path)]
    except KeyError:
        raise ValueError(path) from None


sys.modules["unrealsdk"].find_object = find_object


class Function:
    def __init__(self, names: tuple, returned: bool = False) -> None:
        self.props = [ns(Name=name, PropertyFlags=0) for name in names]
        if returned:
            self.props.append(ns(Name="ReturnValue", PropertyFlags=0x400))

    def _properties(self) -> list:
        return list(self.props)


PARTS = (hunters.LOOKS[0].upper, *hunters.LOOKS[0].followers)

check("a call's parameters, its return value left out", wear.params(Function(("Class", "bDeferredFinish"), True))
      == ("Class", "bDeferredFinish"))
for path, names in wear.CALLS.items():
    state["objects"][("Function", path)] = Function(names, True)
check("every call as expected: nothing differs", wear.differing() == [] and len(wear.CALLS) == 9)
leader = "/Script/Engine.SkinnedMeshComponent:SetLeaderPoseComponent"
state["objects"][("Function", leader)] = Function(("NewLeaderBoneComponent", "bForceUpdate"))
del state["objects"][("Function", "/Script/AssetRegistry.AssetRegistryHelpers:GetAsset")]
check("a call with other parameters, a call missing: both listed", wear.differing() == [
      "SetLeaderPoseComponent", "GetAsset"])
check("the expected parameters, as the game names them (the trials' own)", wear.CALLS[leader] == (
      "NewLeaderBoneComponent", "bForceUpdate", "bInFollowerShouldTickPose")
      and wear.CALLS["/Script/Engine.Actor:AddComponentByClass"] == (
          "Class", "bManualAttachment", "RelativeTransform", "bDeferredFinish")
      and wear.CALLS["/Script/Engine.PrimitiveComponent:SetMaterial"] == ("ElementIndex", "Material")
      and wear.CALLS["/Script/Engine.Actor:SetActorHiddenInGame"] == ("bNewHidden",))

held = ns(SkeletalMeshAsset=None, SkinnedAsset=ns(_path_name=lambda: PARTS[0]))
check("the model a mesh draws, read as the game holds it (in SkinnedAsset), by its full path", wear.model_of(held)
      is held.SkinnedAsset and wear.drawing(held) == PARTS[0] and wear.drawing(ns()) is None
      and wear.model_of(ns()) is None)

asked: list = []
state["classes"].update({
    "SkeletalMesh": ns(_path_name=lambda: "/Script/Engine.SkeletalMesh"),
    "GestaltSkeletalMesh": ns(_path_name=lambda: "/Script/GbxGame.GestaltSkeletalMesh"),
    "AssetRegistryHelpers": ns(ClassDefaultObject=ns(GetAsset=lambda data: asked.append(data))),
    "SkeletalMeshComponent": "ComponentClass"})
data = wear.asset_data("SkeletalMesh", "/Game/A/B/SKPart_X.SKPart_X")
check("the loader's names", data.PackageName == "/Game/A/B/SKPart_X" and data.PackagePath == "/Game/A/B"
      and data.AssetName == "SKPart_X" and data.AssetClassPath.PackageName == "/Script/Engine"
      and data.AssetClassPath.AssetName == "SkeletalMesh")
upper = PARTS[0]
state["objects"][("GestaltSkeletalMesh", upper)] = "UpperModel"
check("a part already loaded, under the second class: found, nothing loaded", wear.load(upper) == "UpperModel"
      and asked == [])
head = PARTS[3]


def get_asset(found: object) -> None:
    asked.append(found)
    if found.AssetClassPath.AssetName == "GestaltSkeletalMesh":
        state["objects"][("GestaltSkeletalMesh", head)] = "HeadModel"


state["classes"]["AssetRegistryHelpers"] = ns(ClassDefaultObject=ns(GetAsset=get_asset))
check("a part not loaded: loaded, found again by its path", wear.load(head) == "HeadModel"
      and [one.AssetName for one in asked] == ["SKPart_CorpoHacker_Base_Head"] * 2)


def refusing(found: object) -> None:
    raise RuntimeError("refused")


state["classes"]["AssetRegistryHelpers"] = ns(ClassDefaultObject=ns(GetAsset=refusing))
check("a part that cannot be loaded, the loader refusing or not: None", wear.load("/Game/None/X.X") is None)
state["classes"]["AssetRegistryHelpers"] = ns(ClassDefaultObject=ns(GetAsset=lambda data: None))
check("loaded but never found by its path: None", wear.load("/Game/None/Y.Y") is None)

calls: list = []


class Made:
    Name = "SkeletalMeshComponent_7"

    def SetSkeletalMeshAsset(self, model: object) -> None:
        calls.append(("model", model))

    def SetMobility(self, mobility: int) -> None:
        calls.append(("mobility", mobility))

    def K2_AttachToComponent(self, *args: object) -> None:
        calls.append(("attach", *args))

    def SetLeaderPoseComponent(self, *args: object) -> None:
        calls.append(("leader", *args))


made, body = Made(), ns(Name="CharacterMesh")
actor = ns(AddComponentByClass=lambda *args: calls.append(("add", *args)) or (made, "out"),
           FinishAddComponent=lambda *args: calls.append(("finish", *args)))
placed = wear.identity()
check("a part hung on the body, in order", wear.wear(actor, body, "Model", placed) is made and calls == [
      ("add", "ComponentClass", True, placed, True), ("model", "Model"), ("mobility", 2),
      ("finish", made, True, placed), ("attach", body, "None", 0, 0, 0, False), ("leader", body, True, False)])
calls.clear()
actor.AddComponentByClass = lambda *args: made
check("the component given alone, not in a pair: hung all the same", wear.wear(actor, body, "M", placed) is made
      and calls[0] == ("model", "M"))
check("the placement: no offset, no turn, its own size", (placed.Rotation.X, placed.Rotation.Y, placed.Rotation.Z,
      placed.Rotation.W) == (0.0, 0.0, 0.0, 1.0) and (placed.Translation.X, placed.Translation.Y,
                                                       placed.Translation.Z) == (0.0, 0.0, 0.0)
      and (placed.Scale3D.X, placed.Scale3D.Y, placed.Scale3D.Z) == (1.0, 1.0, 1.0))
calls.clear()
wear.draw(made, "UpperModel")
check("a mesh given the model, nothing else called", calls == [("model", "UpperModel")])


class Painted:
    def __init__(self) -> None:
        self.calls: list = []

    def SetMaterial(self, index: int, material: object) -> None:
        self.calls.append((index, material))


painted = Painted()
dressed = ns(Materials=[ns(MaterialSlotName=f"S{i}", MaterialInterface=f"MI_{i}") for i in range(3)])
check("each of the model's slots given its own material back, in order", wear.repaint(painted, dressed, 24) == 3
      and painted.calls == [(0, "MI_0"), (1, "MI_1"), (2, "MI_2")])
painted.calls.clear()
check("no more slots than the limit", wear.repaint(painted, dressed, 2) == 2 and len(painted.calls) == 2)

flags: list = []
character = ns(SetActorHiddenInGame=flags.append)
wear.hide(character, True)
wear.hide(character, False)
check("the whole character hidden, then shown, by its own flag", flags == [True, False])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
