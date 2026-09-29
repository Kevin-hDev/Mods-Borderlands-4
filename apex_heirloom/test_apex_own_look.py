"""Tests our knife's own look: each slot of the look gets its own copy of the game's material, found by its path as a
material instance, named after the slot, with every value the look sets, each by name, association and index: a
number, a colour by its four channels, a texture loaded by its path; each call to the engine said before it is made;
a slot our model lacks, a material or a texture not found, left and said; a failure said, the other slots dressed; and
the knife's own look in the mod's catalog is the Jakobs knife's, as its heirloom.json sets it."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import definition_fixture  # noqa: E402
import heirloom_stubs  # noqa: E402

heirloom_stubs.install()
from apex_heirloom import apex_own_look as look  # noqa: E402
from apex_heirloom.heirloom_catalog import HEIRLOOMS  # noqa: E402

SLOTS = HEIRLOOMS["jakobs_knife"]["skins"][0]["slots"]

fails: list[str] = []
said: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Copy:
    """A dynamic material instance: the values set on it, in order, and what it is made from."""

    def __init__(self, parent: object, name: str) -> None:
        self.parent, self.name, self.values = parent, name, []

    def _path_name(self) -> str:
        return f"/Game/Maps/World_P:PersistentLevel.Knife.{self.name}"

    def SetScalarParameterValueByInfo(self, info: object, value: float) -> None:
        self.values.append(("scalar", info, value))

    def SetVectorParameterValueByInfo(self, info: object, value: object) -> None:
        self.values.append(("vector", info, value))

    def SetTextureParameterValueByInfo(self, info: object, value: object) -> None:
        self.values.append(("texture", info, value))


class Knife:
    """Our model's component: its slots by name, and the copies made in them."""

    def __init__(self, slots: list[str]) -> None:
        self.slots, self.made = slots, {}

    def GetMaterialIndex(self, name: str) -> int:
        return self.slots.index(name) if name in self.slots else -1

    def CreateDynamicMaterialInstance(self, index: int, parent: object, name: str) -> Copy:
        if getattr(parent, "broken", False):
            raise RuntimeError("the engine refused")
        said.append(f"(engine) copy made in slot {index}")
        self.made[index] = Copy(parent, name)
        return self.made[index]


assets: dict[tuple[str, str], object] = {}


def load(class_name: str, path: str) -> object:
    return assets.get((class_name, path))


def asset(path: str, **fields: object) -> object:
    return types.SimpleNamespace(_path_name=lambda: path, **fields)


RUINS, GLASS = "/Game/Gear/M_LEG_01_Ruins.M_LEG_01_Ruins", "/Game/Gear/M_LEG_01_Ruins_Glass.M_LEG_01_Ruins_Glass"
C1 = "/Game/Gear/T_JAK_GRN_C1.T_JAK_GRN_C1"
slots = {
    "Base_Mat": {"parent": RUINS,
                 "scalars": [{"name": "JAK_Filigree_Tiling", "association": 0, "index": 0, "value": 22.0}],
                 "vectors": [{"name": "DL_Placement", "association": 2, "index": -1, "value": [-5.0, 0.0, 0.25, 1.0]}],
                 "textures": [{"name": "C1", "association": 2, "index": -1, "value": C1}]},
    "Tech_Mat": {"parent": GLASS, "scalars": [{"name": "Wear", "association": 2, "index": -1, "value": 0.0}]},
}
assets.update({("MaterialInstanceConstant", RUINS): asset(RUINS), ("MaterialInstanceConstant", GLASS): asset(GLASS),
               ("Texture2D", C1): asset(C1)})
knife = Knife(["Tech_Mat", "Base_Mat"])
check("both slots dressed", look.dress(knife, slots, load, said.append) == 2)
base, tech = knife.made[1], knife.made[0]
check("each slot gets its own copy of the game's material the look names, found as a material instance, named after "
      "the slot, whatever the slot numbers", base.parent is assets[("MaterialInstanceConstant", RUINS)]
      and tech.parent is assets[("MaterialInstanceConstant", GLASS)] and base.name == "MID_ApexHeirloom_Base_Mat")
kind, info, value = base.values[0]
check("a number set by name, association and index: a layer's value reaches its layer",
      kind == "scalar" and (info.Name, info.Association, info.Index, value) == ("JAK_Filigree_Tiling", 0, 0, 22.0))
kind, info, value = base.values[1]
check("a colour by its four channels", kind == "vector" and info.Name == "DL_Placement"
      and (value.R, value.G, value.B, value.A) == (-5.0, 0.0, 0.25, 1.0))
kind, info, value = base.values[2]
check("a texture loaded by its path", kind == "texture" and info.Name == "C1"
      and value is assets[("Texture2D", C1)])
check("each call to the engine said before it is made, then what was done",
      said.index(f"slot Base_Mat: CreateDynamicMaterialInstance from {RUINS}") + 1
      == said.index("(engine) copy made in slot 1")
      and "slot Base_Mat: setting the look's values on /Game/Maps/World_P:PersistentLevel.Knife.MID_ApexHeirloom_"
      "Base_Mat" in said and "slot Base_Mat: dressed, 3 values set" in said)

said.clear()
del assets[("Texture2D", C1)]
knife = Knife(["Base_Mat"])
check("a slot our model lacks is left and said; a texture not found keeps the material's own, said",
      look.dress(knife, slots, load, said.append) == 1 and "slot Tech_Mat: our model has none, left undressed" in said
      and f"texture {C1} not found: C1 keeps the material's own" in said
      and "slot Base_Mat: dressed, 2 values set" in said)
said.clear()
del assets[("MaterialInstanceConstant", RUINS)]
knife = Knife(["Base_Mat", "Tech_Mat"])
check("a material not found: its slot left as it is, said, the other dressed",
      look.dress(knife, slots, load, said.append) == 1 and f"slot Base_Mat: {RUINS} not found, left as it is" in said
      and list(knife.made) == [1])
said.clear()
assets[("MaterialInstanceConstant", RUINS)] = asset(RUINS, broken=True)
knife = Knife(["Base_Mat", "Tech_Mat"])
check("a copy the engine refuses: said, the other slot dressed", look.dress(knife, slots, load, said.append) == 1
      and "slot Base_Mat: could not be dressed: RuntimeError('the engine refused')" in said and list(knife.made) == [1])

definition = definition_fixture.load()
if definition is None:
    definition_fixture.skip("the knife's own look in the mod's catalog is the one its heirloom.json sets")
else:
    check("the knife's own look in the mod's catalog is the one its heirloom.json sets",
          SLOTS == definition["look"]["slots"])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
