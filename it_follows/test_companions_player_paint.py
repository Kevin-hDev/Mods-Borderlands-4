"""Tests the player's colours on a hunter companion (companions/player_paint.py): the player's meshes listed only
while the call's parameters are trial 160's, MAX_MESHES at most; the materials the game made for them gathered by
the one each was made from, the first one kept, any other kind or a slot unread left out; the hunter played read
from the code name the most of them bear, in their folder or their name, none when none bears one, the mouth's
shared one counting for no one; each slot of a model whose own material one of them was made from given it, the
others left, how many said; read from the player's controller, a controller without a character naming no one.
His head: the first part his body merges lying in a heads' folder; put in place of the base head only when
it lies in that hunter's folder."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows.companions import hunters, player_paint  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def ns(**fields: object) -> types.SimpleNamespace:
    return types.SimpleNamespace(**fields)


def find_object(kind: str, path: str) -> object:
    try:
        return state["objects"][(kind, path)]
    except KeyError:
        raise ValueError(path) from None


sys.modules["unrealsdk"].find_object = find_object
state["classes"]["SkeletalMeshComponent"] = "the class"


def lister(*names: str) -> None:
    state["objects"][("Function", player_paint.LISTER)] = ns(_properties=lambda: [
        ns(Name=name, PropertyFlags=0) for name in names])


def thing(path: str, kind: str = "MaterialInstanceConstant", parent: object = None) -> types.SimpleNamespace:
    return ns(_path_name=lambda: path, Class=ns(Name=kind), Parent=parent)


VEX_U = "/Game/PlayerCharacters/DarkSiren/_Shared/Materials/MI_DarkSiren_U.MI_DarkSiren_U"
VEX_L = "/Game/Elsewhere/MI_DarkSiren_L.MI_DarkSiren_L"
MOUTH = "/Game/Characters/_Shared/MI_Template_Char_Mouth.MI_Template_Char_Mouth"
made_u = thing("/Engine/Transient.MID_MI_DarkSiren_U", "MaterialInstanceDynamic", thing(VEX_U))
again_u = thing("/Engine/Transient.MID_again", "MaterialInstanceDynamic", thing(VEX_U))
made_l = thing("/Engine/Transient.MID_MI_DarkSiren_L", "MaterialInstanceDynamic", thing(VEX_L))
made_mouth = thing("/Engine/Transient.MID_Mouth", "MaterialInstanceDynamic", thing(MOUTH))
plain = thing("/Game/Plain.MI_Plain", "MaterialInstanceConstant", thing("/Game/PlayerCharacters/DarkSiren/MI_Own.X"))
orphan = thing("/Engine/Transient.MID_orphan", "MaterialInstanceDynamic", None)


class Unread:
    @property
    def OverrideMaterials(self) -> list:
        raise RuntimeError("no")


player_meshes = [ns(OverrideMaterials=[made_u, None, plain, orphan]), Unread(),
                 ns(OverrideMaterials=[again_u, made_l, made_mouth])]
asked: list = []
character = ns(K2_GetComponentsByClass=lambda kind: asked.append(kind) or iter(player_meshes))

lister("Other")
check("the call's parameters not trial 160's: no mesh, the call never made", player_paint.meshes(character) == []
      and asked == [])
lister("ComponentClass")
check("its parameters: the player's meshes, of the mesh class", player_paint.meshes(character) == player_meshes
      and asked == ["the class"])
many = ns(K2_GetComponentsByClass=lambda kind: iter(range(100)))
check("MAX_MESHES at most", len(player_paint.meshes(many)) == player_paint.MAX_MESHES)

paints = player_paint.paints(player_meshes)
check("the materials made for him, by the one each was made from, the first kept; others and unread left out",
      paints == {VEX_U: made_u, VEX_L: made_l, MOUTH: made_mouth})
check("a hunter's code name, from his upper body", [player_paint.code(look) for look in hunters.LOOKS] == [
      "CorpoHacker", "ExoSoldier", "DarkSiren", "Paladin", "Gravitar", "RoboDealer"])
check("borne in its folder or in its own name, never in a longer word", player_paint.bears(VEX_U, "DarkSiren")
      and player_paint.bears(VEX_L, "DarkSiren") and not player_paint.bears(MOUTH, "DarkSiren")
      and not player_paint.bears("/Game/X/MI_DarkSirenish_U.MI_DarkSirenish_U", "DarkSiren"))
check("the hunter played: the one the most of them bear", player_paint.played(paints) == "Vex")
check("the mouth's alone, or nothing: no one", player_paint.played({MOUTH: made_mouth}) is None
      and player_paint.played({}) is None)
check("two hunters: the one most borne", player_paint.played({
      "/Game/PlayerCharacters/Paladin/A.A": 1, "/Game/PlayerCharacters/Paladin/B.B": 2, VEX_U: 3}) == "Amon")

body = ns(Materials=[ns(MaterialInterface=thing(VEX_U)), ns(MaterialInterface=thing("/Game/Other.MI_Other")),
                     ns(MaterialInterface=thing(MOUTH)), ns(MaterialInterface=None)])
check("the slots one of them fits: index and the player's one", player_paint.fitting(body, paints) == [
      (0, made_u), (2, made_mouth)])
long_model = ns(Materials=[ns(MaterialInterface=thing(VEX_U))] * 40)
check("MAX_SLOTS at most", len(player_paint.fitting(long_model, paints)) == player_paint.MAX_SLOTS)
set_on: list = []
mesh = ns(SetMaterial=lambda index, material: set_on.append((index, material)))
other = ns(SetMaterial=lambda index, material: set_on.append(("other", index)))
check("painted: each fitting slot given the player's one, the others left, how many",
      player_paint.paint([(mesh, body), (other, ns(Materials=[]))], paints) == 2
      and set_on == [(0, made_u), (2, made_mouth)])

# His vehicle while he drives: the colours are read on his character all the same (review of 22 October 2026).
PC = ns(OakCharacter=character, Pawn=ns(Mesh=ns(GestaltMeshParts=[])))
check("the player's own colours, from his controller's character even while he drives; his body unread: no "
      "head, no part", player_paint.of(PC) == (paints, None, ()))
PREMIUM = "/Game/PlayerCharacters/Customizations/DarkSiren/HeadSwaps/DS_Head_16_Premium/Model/Rig/SK_DS_Head_16.X"
BASE = "/Game/PlayerCharacters/DarkSiren/Heads/Base/Rig/SK_DarkSiren_Base_Head.SK_DarkSiren_Base_Head"
UPPER = "/Game/PlayerCharacters/DarkSiren/_Shared/Model/Rig/SKPart_DarkSiren_UpperBody.X"


class Unnamed:
    def _path_name(self) -> str:
        raise RuntimeError("no")


character.Mesh = ns(GestaltMeshParts=[thing(UPPER), Unnamed(), thing(PREMIUM), thing(BASE)])
check("the parts merged into his body, an unread one left out", player_paint.merged(character) == [
      UPPER, PREMIUM, BASE])
check("MAX_MESHES parts at most", len(player_paint.merged(ns(Mesh=ns(GestaltMeshParts=[thing(UPPER)] * 50))))
      == player_paint.MAX_MESHES)
check("his body unread: no part", player_paint.merged(ns()) == [] and player_paint.merged(None) == [])
check("his head: the first part in a heads' folder", player_paint.head([UPPER, PREMIUM, BASE]) == PREMIUM
      and player_paint.head([BASE]) == BASE and player_paint.head([UPPER]) is None and player_paint.head([]) is None)
check("read with his colours, his parts kept", player_paint.of(PC) == (paints, PREMIUM, (UPPER, PREMIUM, BASE)))
vex, rafa = hunters.BY_NAME["Vex"], hunters.BY_NAME["Rafa"]
check("his head in place of the base one, the other parts kept", player_paint.headed(vex, PREMIUM).followers == (
      vex.followers[0], vex.followers[1], PREMIUM) and player_paint.headed(vex, PREMIUM).upper == vex.upper)
check("no head, or another hunter's: the look itself", player_paint.headed(vex, None) is vex
      and player_paint.headed(rafa, PREMIUM) is rafa
      and player_paint.headed(vex, "/Game/X/DarkSirenish/Heads/A.A") is vex)
check("the hunter he plays, from his controller", player_paint.played_by(PC) == "Vex")
check("a controller without a character: no one, nothing raised", player_paint.played_by(ns(OakCharacter=None)) is None)
check("no controller at all: no one, nothing raised", player_paint.played_by(None) is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
