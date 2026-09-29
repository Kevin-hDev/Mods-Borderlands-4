"""Tests each heirloom's own lists in its fake game: an heirloom's animations' paths in its default mode's folder, each
mode's list in its own, as heirloom.json sets them; an option's condition read by its definition's name, its object's
name or its text; a mode's list given to empty hands once, after the game's, and not twice; another mode's given in
its place; another heirloom's given in its place; an unknown mode or heirloom refused; not given, and said, without
the picker, without its option for empty hands or without the heirloom's container; taken back wherever they are, the
game's list left; the arms said to play an heirloom's only when the rest comes from its folder, and a failure to tell
counted as not, said once."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import definition_fixture  # noqa: E402
import heirloom_stubs  # noqa: E402
from heirloom_stubs import sdk_stubs  # noqa: E402

fails: list[str] = []
said: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def asset(path: str) -> types.SimpleNamespace:
    return types.SimpleNamespace(Name=path.rsplit(".", 1)[1], _path_name=lambda: path)


def choice(condition, *anim_sets) -> types.SimpleNamespace:
    return types.SimpleNamespace(Condition=condition, AnimSets=list(anim_sets))


heirloom_stubs.install()
from apex_heirloom import apex_anim_list as anim_list  # noqa: E402

game_list = asset("/Game/PlayerCharacters/_Shared/Animation/1st/Unarmed/ASet_Player1st_UA.ASet_Player1st_UA")
ours = asset(anim_list.list_path("jakobs_knife", "apex"))
kept = asset(anim_list.list_path("jakobs_knife", "borderlands"))
axe = asset(anim_list.list_path("axe", "apex"))
picker = types.SimpleNamespace(options=[
    choice(types.SimpleNamespace(_name="None"), asset("/Game/Misc.Misc")),
    choice(types.SimpleNamespace(_name="weapon_type_none"), game_list)])
objects = {(anim_list.PICKER_CLASS, anim_list.PICKER): picker}


def find_object(kind: str, path: str):
    if (kind, path) not in objects:
        raise ValueError(path)
    return objects[(kind, path)]


sys.modules["unrealsdk"].find_object = find_object
container = {anim_list.list_path("jakobs_knife", "apex"): ours,
             anim_list.list_path("jakobs_knife", "borderlands"): kept, anim_list.list_path("axe", "apex"): axe}
loads: list[tuple] = []


def load(kind: str, path: str):
    loads.append((kind, path))
    return container.get(path)


definition = definition_fixture.load()
if definition is None:
    definition_fixture.skip("each mode's list folder and the default mode are heirloom.json's")
else:
    lists = definition["lists"]
    check("each mode's list folder and the default mode are heirloom.json's",
          anim_list.DEFAULT_MODE == lists["default"]
          and anim_list.LISTS["jakobs_knife"]["folders"] == {mode: lists[mode]["folder"] for mode in lists
                                                            if mode not in ("why", "default", "container")})
check("an heirloom's animations' paths name its default mode's folder, each list its own",
      anim_list.animation("jakobs_knife", "AS_UA_Equip")
      == "/Game/PlayerCharacters/_Shared/Animation/1st/HeirApx/AS_UA_Equip.AS_UA_Equip"
      and anim_list.list_path("jakobs_knife", "borderlands")
      == "/Game/PlayerCharacters/_Shared/Animation/1st/HeirBrd/ASet_Player1st_UA.ASet_Player1st_UA"
      and anim_list.animation("axe", "AS_UA_Equip")
      == "/Game/PlayerCharacters/_Shared/Animation/1st/AxeApex/AS_UA_Equip.AS_UA_Equip")
check("a condition reads as its definition's name, its object's name, or its text",
      anim_list.condition(choice(types.SimpleNamespace(_name="weapon_type_none"))) == "weapon_type_none"
      and anim_list.condition(choice(types.SimpleNamespace(Name="Cond"))) == "Cond"
      and anim_list.condition(choice("text")) == "text")

check("given once: after the game's list, loaded as a list of animations, said",
      anim_list.add(load, "jakobs_knife", "apex", said.append) and picker.options[1].AnimSets == [game_list, ours]
      and loads == [("GbxAnimSet", anim_list.list_path("jakobs_knife", "apex"))]
      and said[-1].startswith("our jakobs_knife apex animations given to empty hands"))
check("not given twice", anim_list.add(load, "jakobs_knife", "apex", said.append)
      and picker.options[1].AnimSets == [game_list, ours]
      and said[-1] == "our jakobs_knife apex animations were already given to empty hands")
check("another mode's list given in its place", anim_list.add(load, "jakobs_knife", "borderlands", said.append)
      and picker.options[1].AnimSets == [game_list, kept])
check("another heirloom's list given in its place", anim_list.add(load, "axe", "apex", said.append)
      and picker.options[1].AnimSets == [game_list, axe])
check("an unknown mode is refused, the given list left", not anim_list.add(load, "axe", "halo", said.append)
      and said[-1] == "no 'halo' mode: the modes are apex, borderlands"
      and picker.options[1].AnimSets == [game_list, axe])
try:
    unknown_given = anim_list.add(load, "sword", "apex", said.append)
except Exception as error:  # a refusal that breaks is a failure of this check, not of the whole test
    unknown_given = error
check("an unknown heirloom is refused, the given list left", unknown_given is False
      and said[-1] == "no 'sword' heirloom: the heirlooms are jakobs_knife, axe"
      and picker.options[1].AnimSets == [game_list, axe])
picker.options[1].AnimSets.extend([ours, kept])
check("taken back wherever they are, every heirloom's, the game's list left, and counted",
      anim_list.remove(said.append) == 3 and picker.options[1].AnimSets == [game_list]
      and anim_list.remove(said.append) == 0)

del container[anim_list.list_path("axe", "apex")]
check("without the heirloom's container: not given, and said", not anim_list.add(load, "axe", "apex", said.append)
      and picker.options[1].AnimSets == [game_list]
      and f"is {anim_list.LISTS['axe']['container']} installed?" in said[-1])
picker.options[1].Condition._name = "weapon_type_other"
check("without an option for empty hands: not given, and said",
      not anim_list.add(load, "jakobs_knife", "apex", said.append) and "has no weapon_type_none option" in said[-1])
del objects[(anim_list.PICKER_CLASS, anim_list.PICKER)]
check("without the picker: not given, nothing taken, and said",
      not anim_list.add(load, "jakobs_knife", "apex", said.append)
      and anim_list.remove(said.append) == 0 and "picker of arm animations is not loaded" in said[-1])

asked: list[str] = []


def arms_playing(path):
    return types.SimpleNamespace(GetAnimationFromTag=lambda tag: asked.append(tag.TagName) or (
        asset(path) if path else None))


knife_rest = anim_list.animation("jakobs_knife", "AS_UA_Idle")
check("the arms play an heirloom's only when the rest comes from its folder, not another heirloom's",
      anim_list.played(arms_playing(knife_rest), "jakobs_knife", said.append)
      and not anim_list.played(arms_playing(knife_rest), "axe", said.append)
      and anim_list.played(arms_playing(anim_list.animation("axe", "AS_UA_Idle")), "axe", said.append)
      and not anim_list.played(arms_playing(game_list._path_name().replace("ASet_Player1st_UA", "AS_UA_Idle")),
                               "jakobs_knife", said.append)
      and not anim_list.played(arms_playing(None), "jakobs_knife", said.append)
      and asked[0] == "AnimSet.Player.1st.Idle")
said.clear()
check("a failure to tell counts as not, said once",
      not anim_list.played(types.SimpleNamespace(), "jakobs_knife", said.append)
      and not anim_list.played(types.SimpleNamespace(), "jakobs_knife", said.append) and len(said) == 1
      and said[0].startswith("which animations the arms play could not be read"))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
