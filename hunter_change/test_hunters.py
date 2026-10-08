"""The six hunters: in the menu's order with their names, each one's size as measured in game, found by the game's
character name, by code or by the player state that plays one, the body and head of each skin named alike and told
back from their names, and each tree's group as the saves write it."""

import sys
from types import SimpleNamespace

import sdk_stubs

sdk_stubs.install()

from hunter_change import hunters  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("six hunters in the menu's order, with their names",
      [(hunter.code, hunter.name) for hunter in hunters.HUNTERS] == [
          ("DarkSiren", "Vex"), ("ExoSoldier", "Rafa"), ("Gravitar", "Harlowe"), ("Paladin", "Amon"),
          ("RoboDealer", "C4SH"), ("CorpoHacker", "Loveless")])
check("each one's size as measured in its own game (2026-10-08), the view heights those of essai 27",
      {hunter.name: tuple(vars(hunter.stature).values()) for hunter in hunters.HUNTERS} == {
          "Vex": (93.0, 71.0, 39.5, -93.0), "Rafa": (100.0, 77.0, 54.5, -100.0),
          "Harlowe": (86.0, 67.0, 48.5, -87.0), "Amon": (115.0, 102.0, 69.5, -115.0),
          "C4SH": (105.0, 90.0, 62.5, -105.0), "Loveless": (100.0, 81.5, 59.0, -100.0)}
      and {hunter.name: hunter.stature.half + hunter.stature.eye for hunter in hunters.HUNTERS}
      == {"Vex": 164.0, "Rafa": 177.0, "Harlowe": 153.0, "Amon": 217.0, "C4SH": 195.0, "Loveless": 181.5}
      and (hunters.RADIUS, hunters.CROUCHED_HALF) == (40.0, 60.5))
check("found by the game's character name, nothing for another",
      hunters.by_character("Char_ExoSoldier").name == "Rafa" and hunters.by_character("Char_Echo4") is None
      and hunters.by_character("None") is None)
check("found by code, nothing for another", hunters.by_code("Paladin").name == "Amon"
      and hunters.by_code("Gravitar ") is None and hunters.by_code("") is None)
check("the hunter a player state plays, nothing without a player state, a definition or one of the six",
      getattr(hunters, "played", None) is not None
      and hunters.played(SimpleNamespace(ReplicatedCharacterDef="Char_Paladin")) == hunters.by_code("Paladin")
      and hunters.played(None) is None and hunters.played(SimpleNamespace()) is None
      and hunters.played(SimpleNamespace(ReplicatedCharacterDef="Char_Echo4")) is None)
amon, harlowe = hunters.by_code("Paladin"), hunters.by_code("Gravitar")
check("their default parts named alike", hunters.parts(amon) == {
    hunters.BODY: "Cosmetics_Paladin_Body00_Default", hunters.HEAD: "Cosmetics_Paladin_Head00_Default"})
check("the three skins in the window's order", hunters.SKINS == ("default", "prison", "premium"))
check("a body and a head of any skins named as the game's files do, the premium head the 16th",
      hunters.parts(amon, hunters.PREMIUM, hunters.PRISON) == {
          hunters.BODY: "Cosmetics_Paladin_Body02_Premium", hunters.HEAD: "Cosmetics_Paladin_Head01_Prison"}
      and hunters.parts(harlowe, hunters.PRISON, hunters.PREMIUM)[hunters.HEAD] == "Cosmetics_Gravitar_Head16_Premium")
check("every body and head part told back as its hunter and skin",
      all(hunters.part_of(name) == (hunter, skin) for hunter in hunters.HUNTERS for skin in hunters.SKINS
          for name in hunters.parts(hunter, skin, skin).values()))
check("a part of none of the skins told as none",
      hunters.part_of("Cosmetics_ExoSoldier_Head00_Default_Alt") is None and hunters.part_of("") is None
      and hunters.part_of("Cosmetics_Paladin_Head02_Premium") is None)
check("each tree's group as the saves write it",
      {hunter.name: hunter.tree_group for hunter in hunters.HUNTERS}
      == {"Vex": "ProgressGroup_DarkSiren", "Rafa": "progress_group_exo", "Harlowe": "progress_group_gravitar",
          "Amon": "ProgressGroup_Paladin", "C4SH": "ProgressGroup_Robodealer",
          "Loveless": "ProgressGroup_Corpohacker"})

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
