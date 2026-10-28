"""Tests the hunters' looks (companions/hunters.py): the six hunters in order, each with the parts the game built for it
on Harlowe (hunter change, 2026-09-28), jetpack and hook left out, by full path; each known by its name; a path known
without regard to capitals; the hunter an upper body belongs to, none for any other model. The guests (decision 77):
Lilith's six parts, the phoenix's with her wings and her eight materials put over, Moxxi's one model; known by name
and by upper body, never among the hunters of the menu."""

import pathlib
import sys
from importlib import util

HERE = pathlib.Path(__file__).resolve().parent
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


spec = util.spec_from_file_location("hunters_under_test", HERE / "characters" / "companions" / "hunters.py")
hunters = util.module_from_spec(spec)
spec.loader.exec_module(hunters)
LOOKS = hunters.LOOKS


def names(look: object) -> list:
    return [path.rsplit(".", 1)[-1] for path in (look.upper, *look.followers)]


# As the game listed each body (unrealsdk_chasseurs_024925.log, "body now: ... parts"), jetpack and hook left out.
BUILT = {
    "Loveless": ["SKPart_CorpoHacker_UpperBody", "SKPart_CorpoHacker_Lowerbody", "SKPart_CorpoHacker_LowerBody_Cloth",
                 "SKPart_CorpoHacker_Base_Head"],
    "Rafa": ["SKPart_ExoSoldier_UpperBody", "SKPart_ExoSoldier_LowerBody", "SK_ExoSoldier_Base_Head"],
    "Vex": ["SKPart_DarkSiren_UpperBody", "SKPart_DarkSiren_LowerBody", "SKPart_DarkSiren_Jacket",
            "SK_DarkSiren_Base_Head"],
    "Amon": ["SKPart_Paladin_Upperbody", "SKPart_Paladin_Lowerbody", "SK_Paladin_Base_Head"],
    "Harlowe": ["SKPart_Gravitar_UpperBody", "SKPart_Gravitar_LowerBody", "SK_Gravitar_Base_Head"],
    "C4SH": ["SKPart_RoboDealer_UpperBody", "SKPart_RoboDealer_LowerBody", "SK_RoboDealer_Base_Head"]}
check("six hunters, in order", [look.name for look in LOOKS] == ["Loveless", "Rafa", "Vex", "Amon", "Harlowe", "C4SH"])
check("each with the parts the game built for it, upper body first", all(names(look) == BUILT[look.name]
                                                                          for look in LOOKS))
check("full paths, as in the game files", LOOKS[2].upper == "/Game/PlayerCharacters/DarkSiren/_Shared/Model/Rig/"
      "SKPart_DarkSiren_Upperbody.SKPart_DarkSiren_UpperBody" and LOOKS[5].followers[-1] == "/Game/DLC/Cowbell/"
      "PlayerCharacters/RoboDealer/Heads/Base/Rig/SK_RoboDealer_Base_Head.SK_RoboDealer_Base_Head"
      and LOOKS[0].upper == "/Game/DLC/Harmonica/PlayerCharacters/CorpoHacker/_Shared/Model/Rig/"
      "SKPart_CorpoHacker_UpperBody.SKPart_CorpoHacker_UpperBody"
      and all(path.startswith("/Game/") and path.count(".") == 1 for look in LOOKS
              for path in (look.upper, *look.followers)))
check("each known by its name, the hunters then the guests", list(hunters.BY_NAME) == [*BUILT, "Lilith",
      "Lilith Phoenix", "Moxxi"] and hunters.BY_NAME["Amon"] is LOOKS[3]
      and hunters.BY_NAME["Moxxi"] is hunters.GUESTS[2])
check("the hunters wear no paints over their own materials", all(look.paints == () for look in LOOKS))

GUESTS = hunters.GUESTS
LILITH_RIG = "/Game/AI/NPC/_Unique/Lilith/Model/Rig/"
# GPartList_NPC_Lilith's parts, body first (docs/renforts/releves/2026-10-24-lilith-et-moxxi/pieces/).
LILITH = ["SKPart_Lilith_Body", "SKPart_Lilith_Head", "SKPart_Lilith_Hair", "SKPart_Lilith_Outfit_01",
          "SKPart_Lilith_Eyes", "SKPart_Lilith_Teeth"]
check("the guests: Lilith, Lilith as the phoenix, Moxxi; none of them a companion of the menu",
      [look.name for look in GUESTS] == ["Lilith", "Lilith Phoenix", "Moxxi"]
      and not set(GUESTS) & set(LOOKS))
check("Lilith: her part list's six parts, the body first, by full path", names(GUESTS[0]) == LILITH
      and GUESTS[0].upper == f"{LILITH_RIG}SKPart_Lilith_Body.SKPart_Lilith_Body" and GUESTS[0].paints == ())
check("the phoenix: the same parts and her wings", names(GUESTS[1]) == [*LILITH, "SKPart_Lilith_Wings"]
      and GUESTS[1].upper == GUESTS[0].upper)
PHOENIX = dict(GUESTS[1].paints)
MATERIALS = "/Game/AI/NPC/_Unique/Lilith/Model/Materials/"
check("the phoenix's paints: each of Lilith's own materials to its phoenix one, by full path",
      len(PHOENIX) == 8 and PHOENIX[f"{MATERIALS}MI_Lilith_Skin.MI_Lilith_Skin"]
      == f"{MATERIALS}LilithPhoenix/MI_Lilith_Skin_Phoenix.MI_Lilith_Skin_Phoenix"
      and PHOENIX[f"{MATERIALS}MI_Lilith_Eye.MI_Lilith_Eye"]
      == f"{MATERIALS}LilithPhoenix/MI_Lilith_Eye_PHoenix.MI_Lilith_Eye_PHoenix"
      and PHOENIX[f"{MATERIALS}MI_Lilith_Wings.MI_Lilith_Wings"].endswith("MI_Lilith_Wings_Phoenix_Full")
      and PHOENIX[f"{MATERIALS}MI_Lilith_Lowerbody_Normal.MI_Lilith_Lowerbody_Normal"].endswith("_Lowerbody_Phoenix")
      and all(own.startswith(MATERIALS) and own.count("/") == put.count("/") - 1
              and put.startswith(f"{MATERIALS}LilithPhoenix/") for own, put in PHOENIX.items()))
check("Moxxi: one model, nothing to hang", GUESTS[2].upper == "/Game/AI/NPC/_Unique/Moxxi/Model/Rig/SK_Moxxi.SK_Moxxi"
      and GUESTS[2].followers == () and GUESTS[2].paints == ())
check("a guest's upper body known as hers; Lilith's for her two forms the first", hunters.wearing(
      GUESTS[2].upper.lower()) is GUESTS[2] and hunters.wearing(GUESTS[1].upper) is GUESTS[0])
check("a path known without regard to capitals", hunters.same(LOOKS[2].upper.lower(), LOOKS[2].upper)
      and not hunters.same(None, LOOKS[2].upper) and not hunters.same(LOOKS[1].upper, LOOKS[2].upper)
      and not hunters.same(LOOKS[2].upper[:-1], LOOKS[2].upper))
check("the hunter an upper body belongs to; none for his own or a part", hunters.wearing(LOOKS[3].upper.upper())
      is LOOKS[3] and hunters.wearing("/Engine/Transient.Transient_Gestalt") is None
      and hunters.wearing(LOOKS[3].followers[0]) is None and hunters.wearing(None) is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
