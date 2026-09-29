"""The six hunters: in the menu's order with their names, each view height as measured in game, found by the game's
character name, by code or by the player state that plays one, their default parts named alike, the first-person legs
scaled down only for a taller hunter worn, and each tree's group as the saves write it."""

import math
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
check("each view height as measured in game (essai 27)",
      {hunter.name: hunter.view_height for hunter in hunters.HUNTERS}
      == {"Vex": 164.0, "Rafa": 177.0, "Harlowe": 153.0, "Amon": 217.0, "C4SH": 195.0, "Loveless": 181.5})
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
check("the legs scaled down in the ratio of the view heights for a taller hunter worn (essai 26)",
      math.isclose(hunters.legs_scale(harlowe, amon), 153.0 / 217.0))
check("the legs kept whole for a smaller hunter worn or the own look",
      hunters.legs_scale(amon, harlowe) == 1.0 and hunters.legs_scale(harlowe, harlowe) == 1.0)
check("each tree's group as the saves write it",
      {hunter.name: hunter.tree_group for hunter in hunters.HUNTERS}
      == {"Vex": "ProgressGroup_DarkSiren", "Rafa": "progress_group_exo", "Harlowe": "progress_group_gravitar",
          "Amon": "ProgressGroup_Paladin", "C4SH": "ProgressGroup_Robodealer",
          "Loveless": "ProgressGroup_Corpohacker"})

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
