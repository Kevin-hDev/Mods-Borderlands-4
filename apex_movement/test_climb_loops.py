"""Tests the choice of the body's climb loop: the hunter read first in the character's definition, then the first of
its loops in memory, as the game's files hold them (2026-10-25); each miss said once, by name."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import climb_loops  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def character(definition: str) -> object:
    return types.SimpleNamespace(GbxActorData=types.SimpleNamespace(GbxActorDef=definition))


def skills(folder: str, name: str) -> str:
    return f"/Game/{folder}Animation/3rd/CharacterSkills/{name}.{name}"


# The game's files, read with the extractor on 2026-10-25 (releves/apex_movement/2026-10-25-grimpe-corps-chasseurs/
# extraction/): only Vex and C4SH have AS_Wall_Climb_U in third person; every hunter has AS_Ladder_Ascend.
FOLDERS = {
    "DarkSiren": "PlayerCharacters/DarkSiren/",
    "RoboDealer": "DLC/Cowbell/PlayerCharacters/RoboDealer/",
    "Paladin": "PlayerCharacters/Paladin/",
    "ExoSoldier": "PlayerCharacters/ExoSoldier/",
    "Gravitar": "PlayerCharacters/Gravitar/",
    "CorpoHacker": "DLC/Harmonica/PlayerCharacters/CorpoHacker/",
}
WALL_FIRST = ("DarkSiren", "RoboDealer")
check("six hunters, known by their class", set(climb_loops.LOOPS) == set(FOLDERS))
check("Vex and C4SH: their wall climb first, their ladder ascent after",
      all(climb_loops.LOOPS.get(hunter) == (skills(FOLDERS[hunter], "AS_Wall_Climb_U"),
                                            skills(FOLDERS[hunter], "AS_Ladder_Ascend")) for hunter in WALL_FIRST))
check("the four others: their own ladder ascent only",
      all(climb_loops.LOOPS.get(hunter) == (skills(FOLDERS[hunter], "AS_Ladder_Ascend"),)
          for hunter in FOLDERS if hunter not in WALL_FIRST))

check("the hunter is the definition's first class",
      climb_loops.hunter(character("FGbxDefPtr('Char_Paladin', /Script/GbxGame.GbxActorDef)")) == "Paladin")
check("Loveless, though her definition names Vex further in",
      climb_loops.hunter(character("FGbxDefPtr('Char_CorpoHacker', ... Char_DarkSiren ...)")) == "CorpoHacker")
check("a definition written without quotes", climb_loops.hunter(character("FGbxDefPtr(Char_RoboDealer, x)"))
      == "RoboDealer")
check("a definition naming no class is unknown", climb_loops.hunter(character("FGbxDefPtr(None)")) == "unknown")

loops = {path: object() for paths in climb_loops.LOOPS.values() for path in paths}
state["objects"].update({("AnimSequence", path): loop for path, loop in loops.items()})
for hunter in FOLDERS:
    first = climb_loops.LOOPS.get(hunter, ("missing",))[0]
    check(f"{hunter}: its first loop is played when in memory",
          climb_loops.loop_for(character(f"FGbxDefPtr('Char_{hunter}', x)")) is loops.get(first))

wall = skills(FOLDERS["RoboDealer"], "AS_Wall_Climb_U")
state["objects"].pop(("AnimSequence", wall), None)
c4sh = character("FGbxDefPtr('Char_RoboDealer', x)")
check("C4SH without his wall climb in memory gets his ladder ascent",
      climb_loops.loop_for(c4sh) is loops.get(skills(FOLDERS["RoboDealer"], "AS_Ladder_Ascend")))

errors = len(state["errors"])
for path in climb_loops.LOOPS.get("RoboDealer", ()) + climb_loops.LOOPS.get("Gravitar", ()):
    state["objects"].pop(("AnimSequence", path), None)
harlowe = character("FGbxDefPtr('Char_Gravitar', x)")
answers = [climb_loops.loop_for(c4sh), climb_loops.loop_for(c4sh), climb_loops.loop_for(harlowe)]
check("no loop in memory: nothing, said once per hunter with every path looked at",
      answers == [None, None, None] and state["errors"][errors:] == [
          f"[Apex Movement] body climb animation unavailable for {hunter}: none in memory of "
          + ", ".join(climb_loops.LOOPS.get(hunter, ())) for hunter in ("RoboDealer", "Gravitar")])

errors = len(state["errors"])
answers = [climb_loops.loop_for(character("FGbxDefPtr('Char_Stranger', x)")) for _ in range(2)]
answers.append(climb_loops.loop_for(character("FGbxDefPtr('Char_Other', x)")))
check("an unknown hunter: nothing, said once each, by name", answers == [None, None, None] and state["errors"][errors:] == [
    "[Apex Movement] body climb animation unavailable: no climb known for Stranger",
    "[Apex Movement] body climb animation unavailable: no climb known for Other"])

errors = len(state["errors"])
check("an unreadable definition: nothing, said once",
      climb_loops.loop_for(types.SimpleNamespace()) is None and climb_loops.loop_for(types.SimpleNamespace()) is None
      and len(state["errors"]) == errors + 1 and "hunter unreadable" in state["errors"][-1])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
