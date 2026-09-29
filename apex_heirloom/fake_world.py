"""A fake game for the heirloom's tests: the player's character and arms, the game's picker of arm animations, our
container's lists and knife, and the game's materials and textures the knife's look names, wired into the fake SDK
(heirloom_stubs.py).

Built from test_apex_hand_model.py's own (2026-09-23 to 26), when the heirloom became a mod: its tests share it.
"""

import importlib.util
import sys
import types
from typing import Any

from heirloom_stubs import HERE, sdk_stubs

MODEL = "/Game/ApexHeirloom/SM_ApexHeirloom_JakKnife.SM_ApexHeirloom_JakKnife"
# The heirlooms the mod ships, read from their module by path: importing the mod's package would build the mod. That
# they are the heirlooms' definitions is outils/test_catalog_module.py's check, where those files are at hand.
_catalog = importlib.util.spec_from_file_location("heirloom_catalog_data", HERE / "apex_heirloom" / "heirloom_catalog.py")
_catalog_module = importlib.util.module_from_spec(_catalog)
_catalog.loader.exec_module(_catalog_module)
HEIRLOOMS = _catalog_module.HEIRLOOMS
LOOK = HEIRLOOMS["jakobs_knife"]["skins"][0]["slots"]
AXE_MODEL = HEIRLOOMS["axe"]["model"]
PICKER = "/Game/PlayerCharacters/_Shared/Animation/ASetPicker_Player1st_Shared.ASetPicker_Player1st_Shared"
APEX_LIST = "/Game/PlayerCharacters/_Shared/Animation/1st/HeirApx/ASet_Player1st_UA.ASet_Player1st_UA"
BORDERLANDS_LIST = APEX_LIST.replace("/HeirApx/", "/HeirBrd/")
AXE_LIST = APEX_LIST.replace("/HeirApx/", "/AxeApex/")
FLAGS = {"bGbxForeground": True, "FirstPersonPrimitiveType": 0, "DepthPriorityGroup": 0,
         "bUseViewOwnerDepthPriorityGroup": False, "ViewOwnerDepthPriorityGroup": 0,
         "bOnlyOwnerSee": True, "bOwnerNoSee": False, "CastShadow": False, "bReceivesDecals": False}
# What a component the character builds holds before anyone sets it: the engine takes the ground's decals by default
# (read on our knife in game, 2026-09-26, cosmetics/heirloom/docs/enquetes/2026-09-26-couteau-pale.md).
ENGINE_DEFAULTS = {"bReceivesDecals": True}


class Slots:
    """Material slots by name, as a primitive component keeps them."""

    def __init__(self, names: list[str], materials: list) -> None:
        self.names, self.materials = names, list(materials)

    def GetMaterialSlotNames(self) -> list[str]:
        return self.names

    def GetMaterialIndex(self, name: str) -> int:
        return self.names.index(name) if name in self.names else -1

    def GetMaterial(self, index: int) -> Any:
        return self.materials[index]

    def SetMaterial(self, index: int, material: Any) -> None:
        self.materials[index] = material


class Copy:
    """A dynamic copy of a game material: what it is made from, its name, and the values set on it, in order."""

    def __init__(self, parent: Any, name: str) -> None:
        self.parent, self.name, self.values = parent, name, []

    def _path_name(self) -> str:
        return f"/Game/Maps/World_P:PersistentLevel.Knife.{self.name}"

    def SetScalarParameterValueByInfo(self, info: Any, value: float) -> None:
        self.values.append((info.Name, value))

    def SetVectorParameterValueByInfo(self, info: Any, value: Any) -> None:
        self.values.append((info.Name, (value.R, value.G, value.B, value.A)))

    def SetTextureParameterValueByInfo(self, info: Any, value: Any) -> None:
        self.values.append((info.Name, value))


class Mesh(Slots):
    """Our knife's component, as the character builds it."""

    def __init__(self) -> None:
        super().__init__(["Base_Mat", "Tech_Mat"], ["grid", "grid"])
        self.model, self.attached, self.destroyed, self.shown = None, [], False, None
        self.flags_when_finished: dict = {}
        for flag in FLAGS:
            setattr(self, flag, ENGINE_DEFAULTS.get(flag))

    @property
    def StaticMesh(self) -> Any:
        return self.model

    def SetStaticMesh(self, model: Any) -> bool:
        """The engine's: false for the model the component already holds; a new model brings its own slots."""
        if model is self.model:
            return False
        self.model = model
        self.names, self.materials = list(model.slots), ["grid"] * len(model.slots)
        return True

    def CreateDynamicMaterialInstance(self, index: int, parent: Any, name: str) -> Copy:
        self.materials[index] = Copy(parent, name)
        return self.materials[index]

    def SetMobility(self, _value: Any) -> None:
        pass

    def SetVisibility(self, shown: bool, *_a: Any) -> None:
        self.shown = shown

    def SetRelativeScale3D(self, scale: Any) -> None:
        self.fitted_scale = (scale.X, scale.Y, scale.Z)

    def K2_SetRelativeRotation(self, rotator: Any, *_a: Any) -> None:
        self.fitted_turn = (rotator.Roll, rotator.Pitch, rotator.Yaw)

    def K2_SetRelativeLocation(self, where: Any, *_a: Any) -> None:
        self.fitted_spot = (where.X, where.Y, where.Z)

    def K2_AttachToComponent(self, parent: Any, socket: str, *rules: Any) -> None:
        self.attached.append((parent, socket, rules))

    def K2_DetachFromComponent(self, *_a: Any) -> None:
        pass

    def GetOwner(self) -> Any:
        return self

    def K2_DestroyComponent(self, _owner: Any) -> None:
        self.destroyed = True

    def K2_GetComponentScale(self) -> Any:
        return sdk_stubs.vector(1.0, -1.0, 1.0)


def material(path: str) -> Any:
    return types.SimpleNamespace(_path_name=lambda: path)


class World:
    """The game as the heirloom sees it. `rest` names the folder the arms' rest comes from: ours once the game has read
    our list; `loaded` the packages the engine's loader has brought from our container."""

    def __init__(self, state: dict) -> None:
        self.state, self.meshes, self.loaded, self.rest = state, [], [], ["HeirApx"]
        state["classes"]["KismetMathLibrary"] = types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(
            GreaterGreater_VectorRotator=lambda vector, _rotator: sdk_stubs.vector(vector.X, vector.Y, vector.Z)))
        state["classes"]["StaticMeshComponent"] = object()
        state["classes"]["StaticMesh"] = types.SimpleNamespace(_path_name=lambda: "/Script/Engine.StaticMesh")
        state["classes"]["GbxAnimSet"] = types.SimpleNamespace(_path_name=lambda: "/Script/GbxEngine.GbxAnimSet")
        state["classes"]["AnimSequence"] = types.SimpleNamespace(_path_name=lambda: "/Script/Engine.AnimSequence")
        for kind in ("MaterialInstanceConstant", "Texture2D"):
            state["classes"][kind] = types.SimpleNamespace(_path_name=lambda kind=kind: f"/Script/Engine.{kind}")
        self.knife = types.SimpleNamespace(Name="SM_ApexHeirloom_JakKnife", _path_name=lambda: MODEL,
                                           slots=["Base_Mat", "Tech_Mat"])
        self.axe = types.SimpleNamespace(Name="SM_ApexHeirloom_AxePainted", _path_name=lambda: AXE_MODEL,
                                         slots=["Skin"])
        self.game_list = types.SimpleNamespace(
            _path_name=lambda: "/Game/1st/Unarmed/ASet_Player1st_UA.ASet_Player1st_UA")
        self.apex_list = types.SimpleNamespace(_path_name=lambda: APEX_LIST)
        self.borderlands_list = types.SimpleNamespace(_path_name=lambda: BORDERLANDS_LIST)
        self.axe_list = types.SimpleNamespace(_path_name=lambda: AXE_LIST)
        self.unarmed = types.SimpleNamespace(Condition=types.SimpleNamespace(_name="weapon_type_none"),
                                             AnimSets=[self.game_list])
        self.picker = types.SimpleNamespace(options=[self.unarmed])
        self.container = {MODEL: self.knife, APEX_LIST: self.apex_list, BORDERLANDS_LIST: self.borderlands_list,
                          AXE_LIST: self.axe_list, AXE_MODEL: self.axe}
        sdk_stubs.asset_registry(state, lambda data: self.loaded.append(data.PackageName))
        sys.modules["unrealsdk"].find_object = self.find_object
        # The game's materials and textures every heirloom's skins name, each in its own package of the game's files.
        self.look = {path: material(path) for known in HEIRLOOMS.values() for skin in known["skins"]
                     for recipe in skin["slots"].values()
                     for path in [recipe["parent"]] + [texture["value"] for texture in recipe.get("textures", [])]}
        self.container.update(self.look)
        self.character, self.arms, self.instance = self.new_character()
        # Through the player's eyes, whoever the player is.
        self.camera = types.SimpleNamespace(GetCameraLocation=lambda: sdk_stubs.vector(0.0, 0.0, 0.0),
                                            GetActorCameraMode=lambda _character: "Default",
                                            ViewTarget=types.SimpleNamespace(Target=None))
        state["pc"] = types.SimpleNamespace(OakCharacter=self.character, PlayerCameraManager=self.camera)

    def find_object(self, _cls: Any, path: str) -> Any:
        if path == PICKER:
            return self.picker
        if path in self.container and path.rsplit(".", 1)[0] in self.loaded:
            return self.container[path]
        raise ValueError(path)

    def new_character(self) -> tuple[Any, Any, Any]:
        """A character with no weapon in hand, its arms and their animation, which the game lists."""
        instance = types.SimpleNamespace(GetAnimationFromTag=lambda tag: types.SimpleNamespace(
            _path_name=lambda: f"/Game/PlayerCharacters/_Shared/Animation/1st/{self.rest[0]}/AS_UA_Idle.AS_UA_Idle"),
            GetCurrentActiveMontage=lambda: None)
        anchor = types.SimpleNamespace(Translation=sdk_stubs.vector(0.0, 50.9, 0.0),
                                       Scale3D=sdk_stubs.vector(1.0, 1.0, 1.0))
        arms = types.SimpleNamespace(Name="FirstPersonArms", GetAnimInstance=lambda: instance,
                                     GetAllSocketNames=lambda: ["L_Hand_Object", "R_Hand_Object"],
                                     GetSocketTransform=lambda _s, _w: anchor,
                                     K2_GetComponentScale=lambda: sdk_stubs.vector(1.0, 1.0, 1.0), **FLAGS)
        instance.Outer = arms
        character = types.SimpleNamespace(
            ActiveWeapons=types.SimpleNamespace(Slots=[types.SimpleNamespace(Weapon=None)]),
            CharacterMovement=types.SimpleNamespace(
                LadderState=types.SimpleNamespace(CurrentClimbable=None),
                ReplicatedMantleState=types.SimpleNamespace(ActionIndex=-1)),
            FinishAddComponent=self.finish)
        character.AddComponentByClass = lambda *args: self.meshes.append(Mesh()) or self.meshes[-1]
        arms.Outer = character
        instance.OakCharacter = character
        self.state["all"]["/Script/Engine.AnimInstance"] = [instance]
        return character, arms, instance

    @staticmethod
    def finish(made: Any, *_a: Any) -> None:
        made.flags_when_finished = {flag: getattr(made, flag) for flag in FLAGS}

    def said(self, text: str) -> bool:
        return any(text in line for line in self.state["info"])

    def raw_hook(self, name: str) -> Any:
        """The heirloom's own hook on the arms' animation whose path ends so, while it is on."""
        return next((callback for (path, _k, _i), callback in self.state["raw_hooks"].items() if path.endswith(name)),
                    None)

    def weapon_change(self, weapon: Any) -> None:
        """The player's weapon becomes `weapon` (None: put away), and the arms say so."""
        self.character.ActiveWeapons.Slots[0].Weapon = weapon
        self.raw_hook("OnWeaponChanged")(self.instance, types.SimpleNamespace(NewWeapon=weapon), None, None)

    def frame(self) -> None:
        """One frame of the player's arms, as the heirloom's watch sees it."""
        self.raw_hook("BlueprintUpdateAnimation")(self.instance, None, None, None)
