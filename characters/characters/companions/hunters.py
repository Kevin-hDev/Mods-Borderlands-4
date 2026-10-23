"""The six hunters' default looks, which Lemmy wears to be a hunter companion: the only place that names their parts
(docs/renforts/sondes/hunter_looks.py reads them here).

A hunter cannot be born as a companion: he is not in the game's list of characters to spawn (decision 18 of
docs/renforts/README.md). Lemmy can, and he fights; he wears a hunter's look instead (trials 156 to 159, vérifié en
jeu). Each look: the upper body, which Lemmy's own mesh draws on that hunter's skeleton, then the parts that follow
it. The part names are the ones the game built on Harlowe for each hunter's default body and head (hunter change,
docs/reverse-and-change-hunters/releves/2026-09-28-seance-26/unrealsdk_chasseurs_024925.log), jetpack and grappling
hook left out; their full paths are read in the game files (docs/enemies/donnees/ncs/). The game writes some package
and asset names with other capitals (SKPart_DarkSiren_Upperbody.SKPart_DarkSiren_UpperBody): paths are compared
without capitals (same).
"""

from typing import NamedTuple

GAME = "/Game/PlayerCharacters/"
LOVELESS = "/Game/DLC/Harmonica/PlayerCharacters/CorpoHacker/"
C4SH = "/Game/DLC/Cowbell/PlayerCharacters/RoboDealer/"


class Look(NamedTuple):
    name: str
    upper: str
    followers: tuple


def _rig(root: str, package: str, asset: str = "") -> str:
    return f"{root}_Shared/Model/Rig/{package}.{asset or package}"


def _head(root: str, name: str) -> str:
    return f"{root}Heads/Base/Rig/{name}.{name}"


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
BY_NAME = {look.name: look for look in LOOKS}


def same(path: object, other: str) -> bool:
    return isinstance(path, str) and path.lower() == other.lower()


def wearing(path: object) -> Look | None:
    """The look whose upper body that is; None for any other model, his own among them."""
    return next((look for look in LOOKS if same(path, look.upper)), None)
