"""The looks Lemmy wears: the six hunters' default ones, which make the hunter companions, and the guests', the game's
other characters (Lilith, under her two forms, and Moxxi). The only place that names their parts
(docs/renforts/sondes/hunter_looks.py and run_renforts_guests.py read them here).

A hunter cannot be born as a companion: he is not in the game's list of characters to spawn (decision 18 of
docs/renforts/README.md). Lemmy can, and he fights; he wears a hunter's look instead (trials 156 to 159, vérifié en
jeu). Each look: the upper body, which Lemmy's own mesh draws on that hunter's skeleton, then the parts that follow
it. The part names are the ones the game built on Harlowe for each hunter's default body and head (hunter change,
docs/reverse-and-change-hunters/releves/2026-09-28-seance-26/unrealsdk_chasseurs_024925.log), jetpack and grappling
hook left out; their full paths are read in the game files (docs/enemies/donnees/ncs/). The game writes some package
and asset names with other capitals (SKPart_DarkSiren_Upperbody.SKPart_DarkSiren_UpperBody): paths are compared
without capitals (same).

The guests (decision 77): their records give them nothing to fight with, so Lemmy wears their look too
(docs/renforts/enquetes/2026-10-24-lilith-et-moxxi.md, read in the game files, not seen in game yet). Lilith: her
part list's six parts (GPartList_NPC_Lilith), the body first. As the phoenix: the same with her wings, each
material put over by its phoenix one (LilithPhoenix/), matched by their names: the body that says it,
Body_NPC_Lilith_FullPhoenix, cannot be read out of the game (non vérifié). Moxxi: one model, nothing to hang. Trial
224 showed all three right on Lemmy (vérifié en jeu); they are companions of the ALLIES tab (kinds.GUESTS), never
among the hunters of LOOKS, whose outfits follow the hunter the player plays (player_paint.py).
"""

from typing import NamedTuple

GAME = "/Game/PlayerCharacters/"
LOVELESS = "/Game/DLC/Harmonica/PlayerCharacters/CorpoHacker/"
C4SH = "/Game/DLC/Cowbell/PlayerCharacters/RoboDealer/"
NPC = "/Game/AI/NPC/_Unique/"


class Look(NamedTuple):
    name: str
    upper: str
    followers: tuple
    # (a model's own material, the one put over it) pairs, by full path, once each part has its own back.
    paints: tuple = ()


def _rig(root: str, package: str, asset: str = "") -> str:
    return f"{root}_Shared/Model/Rig/{package}.{asset or package}"


def _head(root: str, name: str) -> str:
    return f"{root}Heads/Base/Rig/{name}.{name}"


def _guest(who: str, name: str) -> str:
    return f"{NPC}{who}/Model/Rig/{name}.{name}"


def _phoenix(own: str, put: str) -> tuple[str, str]:
    root = f"{NPC}Lilith/Model/Materials/"
    return f"{root}{own}.{own}", f"{root}LilithPhoenix/{put}.{put}"


LOOKS = (
    Look("Loveless", _rig(LOVELESS, "SKPart_CorpoHacker_UpperBody"), (
        _rig(LOVELESS, "SKPart_CorpoHacker_Lowerbody"), _rig(LOVELESS, "SKPart_CorpoHacker_LowerBody_Cloth"),
        _head(LOVELESS, "SKPart_CorpoHacker_Base_Head"))),
    Look("Rafa", _rig(GAME + "ExoSoldier/", "SKPart_ExoSoldier_UpperBody"), (
        _rig(GAME + "ExoSoldier/", "SKPart_ExoSoldier_LowerBody"),
        _head(GAME + "ExoSoldier/", "SK_ExoSoldier_Base_Head"))),
    Look("Vex", _rig(GAME + "DarkSiren/", "SKPart_DarkSiren_Upperbody", "SKPart_DarkSiren_UpperBody"), (
        _rig(GAME + "DarkSiren/", "SKPart_DarkSiren_Lowerbody", "SKPart_DarkSiren_LowerBody"),
        _rig(GAME + "DarkSiren/", "SKPart_DarkSiren_Jacket"), _head(GAME + "DarkSiren/", "SK_DarkSiren_Base_Head"))),
    Look("Amon", _rig(GAME + "Paladin/", "SKPart_Paladin_Upperbody"), (
        _rig(GAME + "Paladin/", "SKPart_Paladin_Lowerbody"), _head(GAME + "Paladin/", "SK_Paladin_Base_Head"))),
    Look("Harlowe", _rig(GAME + "Gravitar/", "SKPart_Gravitar_UpperBody"), (
        _rig(GAME + "Gravitar/", "SKPart_Gravitar_LowerBody"), _head(GAME + "Gravitar/", "SK_Gravitar_Base_Head"))),
    Look("C4SH", _rig(C4SH, "SKPart_RoboDealer_UpperBody"), (
        _rig(C4SH, "SKPart_RoboDealer_LowerBody"), _head(C4SH, "SK_RoboDealer_Base_Head"))))
LILITH_PARTS = tuple(_guest("Lilith", f"SKPart_Lilith_{part}") for part in ("Head", "Hair", "Outfit_01", "Eyes",
                                                                             "Teeth"))
GUESTS = (
    Look("Lilith", _guest("Lilith", "SKPart_Lilith_Body"), LILITH_PARTS),
    Look("Lilith Phoenix", _guest("Lilith", "SKPart_Lilith_Body"),
         LILITH_PARTS + (_guest("Lilith", "SKPart_Lilith_Wings"),), (
             _phoenix("MI_Lilith_Skin", "MI_Lilith_Skin_Phoenix"),
             _phoenix("MI_Lilith_Lowerbody_Normal", "MI_Lilith_Lowerbody_Phoenix"),
             _phoenix("MI_Lilith_Head", "MI_Lilith_Head__Phoenix"),
             _phoenix("MI_Lilith_Hair_Top", "MI_Lilith_Hair_Top_Phoenix"),
             _phoenix("MI_Lilith_Hair_Bottom", "MI_Lilith_Hair_Bottom_Phoenix"),
             _phoenix("MI_Lilith_Upperbody", "MI_Lilith_Upperbody_Phoenix"),
             _phoenix("MI_Lilith_Eye", "MI_Lilith_Eye_PHoenix"),
             # Three wing materials in the phoenix's folder; _Full chosen for her record's name, FullPhoenix.
             _phoenix("MI_Lilith_Wings", "MI_Lilith_Wings_Phoenix_Full"))),
    Look("Moxxi", _guest("Moxxi", "SK_Moxxi"), ()))
BY_NAME = {look.name: look for look in LOOKS + GUESTS}
# A look's name in a language of the game's texts where it is not the one above (bars_names.py shows it; the aimed
# bar's package writes each one, docs/renforts/sondes/nameplate_trial). Kevin, 24 October 2026, asked « Lilith
# Phoenix » in English and « Lilith Phénix » in French: « oui ok pour Lilith pheanix ».
NAMES = {"Lilith Phoenix": {"fr": "Lilith Phénix"}}


def same(path: object, other: str) -> bool:
    return isinstance(path, str) and path.lower() == other.lower()


def wearing(path: object) -> Look | None:
    """The look whose upper body that is, the first one for Lilith's two forms; None for any other model, his own
    among them."""
    return next((look for look in LOOKS + GUESTS if same(path, look.upper)), None)
