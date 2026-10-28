"""The game as the grapple gun's look meets it, for the tests: our container's objects, loadable through the engine's
AssetRegistryHelpers as in game, and pieces added to the character that record every call made on them."""

import types
from typing import Any

from apex_grapple import look_assets, look_load

KINDS = {look_load.MESH: "/Script/Engine.StaticMesh", look_load.MATERIAL: "/Script/Engine.MaterialInstanceConstant",
         look_load.TEXTURE: "/Script/Engine.Texture2D"}
SLOT_INDEX = 0


class Recorder:
    """Any call made on it is kept, in order, with its arguments; `answers` gives what some of them return."""

    def __init__(self, name: str, answers: dict | None = None) -> None:
        self.name, self.calls, self.answers = name, [], dict(answers or {})

    def __getattr__(self, method: str) -> Any:
        if method.startswith("__"):
            raise AttributeError(method)

        def called(*args: Any) -> Any:
            self.calls.append((method, args))
            answer = self.answers.get(method)
            return answer(*args) if callable(answer) else answer
        return called

    def called(self, method: str) -> list[tuple]:
        return [args for name, args in self.calls if name == method]


def every_asset() -> list[tuple[str, str]]:
    """Every object of our container the look can ask for."""
    wanted = [(look_load.MATERIAL, look_assets.MATERIAL), (look_load.MATERIAL, look_assets.ROPE["halo"]["material"])]
    for piece in look_assets.PIECES.values():
        wanted.append((look_load.MESH, piece["mesh"]))
        wanted += [(look_load.TEXTURE, image["texture"]) for image in piece["textures"]]
    wanted += [(look_load.TEXTURE, image) for image in look_assets.ROPE["halo"]["images"].values()]
    return wanted


def install(state: dict, missing: tuple[str, ...] = ()) -> dict:
    """Our container installed but for `missing` paths: GetAsset brings each object into the game's memory, as the
    engine does. Returns the fixture's own record: the paths asked of GetAsset and the pieces made."""
    record = {"loaded": [], "pieces": [], "materials": [], "container": set(), "fail_on": None}
    record["container"] = {pair for pair in every_asset() if pair[1] not in missing}

    def get_asset(data: Any) -> None:
        path = f"{data.PackageName}.{data.AssetName}"
        record["loaded"].append(path)
        for kind, known in record["container"]:
            if known == path:
                state["objects"][(kind, path)] = types.SimpleNamespace(path=path, kind=kind)

    state["extra_classes"]["AssetRegistryHelpers"] = types.SimpleNamespace(
        ClassDefaultObject=types.SimpleNamespace(GetAsset=get_asset))
    for kind, path in KINDS.items():
        state["extra_classes"][kind] = types.SimpleNamespace(_path_name=lambda path=path: path)
    state["extra_classes"]["StaticMeshComponent"] = types.SimpleNamespace(Name="StaticMeshComponent")
    return record


def dress(character: Any, record: dict, slot_index: int = SLOT_INDEX) -> Any:
    """The character takes pieces by hand, each a Recorder; `record["fail_on"]` names a call that raises."""
    def material(slot: int, parent: Any, name: str) -> Any:
        made = Recorder(name)
        made.parent = parent
        record["materials"].append(made)
        return made

    def add(component_class: Any, manual: bool, transform: Any, deferred: bool) -> Any:
        if record["fail_on"] == "AddComponentByClass":
            raise RuntimeError("the game refused a component")
        made = Recorder(f"piece{len(record['pieces'])}", {
            "GetMaterialIndex": lambda slot: slot_index, "CreateDynamicMaterialInstance": material,
            "GetOwner": lambda: character,
            "K2_GetComponentLocation": lambda: types.SimpleNamespace(X=0.0, Y=0.0, Z=0.0),
            "K2_GetComponentRotation": lambda: types.SimpleNamespace(Pitch=0.0, Yaw=0.0, Roll=0.0)})
        made.transform = transform
        record["pieces"].append(made)
        return made

    character.AddComponentByClass = add
    character.FinishAddComponent = lambda made, manual, transform: None
    return character


def mesh_of(made: Recorder) -> str:
    return made.called("SetStaticMesh")[0][0].path


def shown(pieces: list[Recorder]) -> int:
    return sum(1 for made in pieces if made.called("SetVisibility") and made.called("SetVisibility")[-1][0])


def put_at(made: Recorder) -> tuple:
    where = made.called("K2_SetWorldLocationAndRotation")[-1][0]
    return where.X, where.Y, where.Z
