"""Tests the hunters' looks (companions/hunters.py): the six hunters in order, each with the parts the game built for it
on Harlowe (hunter change, 2026-09-28), jetpack and hook left out, by full path; each known by its name; a path known
without regard to capitals; the hunter an upper body belongs to, none for any other model."""

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
check("each known by its name", list(hunters.BY_NAME) == list(BUILT) and hunters.BY_NAME["Amon"] is LOOKS[3])
check("a path known without regard to capitals", hunters.same(LOOKS[2].upper.lower(), LOOKS[2].upper)
      and not hunters.same(None, LOOKS[2].upper) and not hunters.same(LOOKS[1].upper, LOOKS[2].upper)
      and not hunters.same(LOOKS[2].upper[:-1], LOOKS[2].upper))
check("the hunter an upper body belongs to; none for his own or a part", hunters.wearing(LOOKS[3].upper.upper())
      is LOOKS[3] and hunters.wearing("/Engine/Transient.Transient_Gestalt") is None
      and hunters.wearing(LOOKS[3].followers[0]) is None and hunters.wearing(None) is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
