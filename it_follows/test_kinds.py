"""Tests the kinds of characters on the table the mod ships: the enemies the trials 8d and 8e drew are enemies, the
cats and Psychos walk and the bats fly; a boss is a boss, an NPC other; a name of another case is the same name; an
unknown or empty name has no kind."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows import kinds  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


try:
    drawn = ("Char_CatAdult", "Char_BatBasic", "Char_CatYoung", "Char_CatElder", "Char_BatRanged", "Char_SpliceMelee",
             "Char_PsychoBasic_Male", "Char_GunToterPistol_Male", "Char_SpliceBasic", "Char_GruntPistol")
    check("every kind the trials 8d and 8e drew is an enemy", all(kinds.kind(name)[0] == kinds.ENEMY for name in drawn))
    check("cats and Psychos walk", kinds.kind("Char_CatAdult")[1] and kinds.kind("Char_PsychoBasic_Male")[1])
    check("bats do not walk: they are never told to", kinds.kind("Char_BatBasic")[1] is False)
    check("a boss is a boss", kinds.kind("Char_Bat_Mine_Boss_Destroyer") == (kinds.BOSS, kinds.kind(
        "Char_Bat_Mine_Boss_Destroyer")[1]))
    check("a friendly character is other", kinds.kind("Char_CatYoung_FriendlyMirage")[0] == kinds.OTHER)
    check("a name of another case is the same name", kinds.kind("char_catadult") == kinds.kind("CHAR_CATADULT")
          == kinds.kind("Char_CatAdult"))
    check("an unknown or empty name has no kind", kinds.kind("Char_NoSuchThing") is None and kinds.kind("") is None
          and kinds.kind(None) is None)
    check("the table holds only the three kinds",
          {kind for kind, _walks in kinds.KINDS.values()} == {kinds.ENEMY, kinds.BOSS, kinds.OTHER})
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
