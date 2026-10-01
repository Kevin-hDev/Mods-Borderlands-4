"""Tests our heirloom in the player's hand: our list given to empty hands first, then our knife, loaded through the
engine's loader, built as a static mesh drawn as the arms are, hung on the right hand with its Y reversed, dressed in
its own look made from the game's files, a slot whose material the game lacks left in the grid, at the size the menu
sets, shown only while no weapon is in hand and the arms play our animations; the menu's size and draw applied at the
next weapon change, its mode's list given at once; another heirloom chosen, its list given at once, its model, own
look, glow and hold on the heirloom in hand at once, hidden until the arms play its animations, drawn with its own;
a glow force or a skin chosen, seen at once, another heirloom's skin leaving it as it is, a change that fails written
without stopping the next; each chosen as the window saves it, through its option; the chosen heirloom's inspection
played at a press of its key from its own folder, only while it shows in the empty hand, stopped when a weapon comes
back or the camera leaves the eyes, the knife's none, one not in the game said once; switched off, our list
taken back and the knife staying while the hands hold it, all taken away once it leaves them, and switched on before,
it stays; put on a new character, the old knife leaves the old hands; without our list, our model or the arms,
nothing is built and it is said."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import definition_fixture  # noqa: E402
import heirloom_stubs  # noqa: E402

state = heirloom_stubs.install()
import fake_world  # noqa: E402

world = fake_world.World(state)
from apex_heirloom import heirloom, heirloom_choices, heirloom_settings, mod  # noqa: E402
from fake_arms import Arms  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def package(path: str) -> str:
    return path.rsplit(".", 1)[0]



said = world.said
unarmed = world.unarmed
check("the knife goes in the hand", heirloom.show(world.character))
mesh = world.meshes[-1]
check("our list is given to empty hands first, loaded from our container, after the game's",
      world.loaded[0] == package(fake_world.APEX_LIST) and unarmed.AnimSets == [world.game_list, world.apex_list]
      and said("our jakobs_knife apex animations given to empty hands"))
check("our model is loaded by its path when not yet in memory, and said",
      world.loaded[1] == package(fake_world.MODEL) and said(f"our model is loaded: {fake_world.MODEL}"))
check("it is a static mesh given our model, drawn as the arms are, hung on the right hand",
      mesh.model is world.knife and mesh.flags_when_finished == fake_world.FLAGS
      and mesh.attached[-1][1] == "R_Hand_Object" and said("in the right hand"))
check("it refuses the ground's decals, as the arms do: the dirt of a road no longer paints over it",
      mesh.flags_when_finished["bReceivesDecals"] is False
      and said("draw flag bReceivesDecals: arms False, object False"))
look = fake_world.LOOK
check("it wears its own look: in each slot a copy of the game's material the look names, loaded from the game's files, "
      "with the look's values, textures loaded too",
      [copy.parent for copy in mesh.materials]
      == [world.look[look[slot]["parent"]] for slot in ("Base_Mat", "Tech_Mat")]
      and package(look["Base_Mat"]["parent"]) in world.loaded
      and ("C1", world.look[look["Base_Mat"]["textures"][0]["value"]]) in mesh.materials[0].values
      and len(mesh.materials[1].values) == sum(len(look["Tech_Mat"].get(kind, []))
                                               for kind in ("scalars", "vectors", "textures"))
      and said("slot Tech_Mat: dressed"))
check("it starts in Wraith's hold at the menu's 100 %: 62 %, its Y reversed, the blade's turn, held at 6 cm",
      mesh.fitted_scale == (0.62, -0.62, 0.62) and mesh.fitted_turn == (-41.1, -44.7, 73.8)
      and mesh.fitted_spot == (-0.0, -0.0, -0.62 * 6.0))
check("no weapon in hand and our animations played: shown, the weapon changes and frames watched",
      mesh.shown is True and len(state["raw_hooks"]) == 2)
check("it hangs on this character's hands and on no other's",
      heirloom.holds_for(world.character) and not heirloom.holds_for(types.SimpleNamespace()))

fits = len([line for line in state["info"] if "fit: " in line])
heirloom_settings.SIZES["jakobs_knife"].value, heirloom_settings.draw_start.value = 150, 0.1
check("the menu's size and draw wait for the next weapon change",
      mesh.fitted_scale[0] == 0.62 and heirloom.STATE.timing.start == 0.4)
world.weapon_change(types.SimpleNamespace(Name="OakWeapon_1"))
world.weapon_change(None)
check("at the next weapon change the knife takes the size, and the draw the start, the menu sets",
      mesh.fitted_scale == (0.93, -0.93, 0.93) and heirloom.STATE.timing.start == 0.1)
world.weapon_change(types.SimpleNamespace(Name="OakWeapon_1"))
world.weapon_change(None)
check("a size already applied is not applied again",
      len([line for line in state["info"] if "fit: " in line]) == fits + 1)
heirloom_settings.SIZES["jakobs_knife"].value, heirloom_settings.draw_start.value = 100, 0.4

heirloom_choices.mode_chosen("Borderlands")
check("a mode chosen gives its list to empty hands at once, in place of the other: the game reads it at the next "
      "weapon change", unarmed.AnimSets == [world.game_list, world.borderlands_list]
      and said("our jakobs_knife borderlands animations given to empty hands"))
heirloom_choices.mode_chosen("Apex")
check("and back", unarmed.AnimSets == [world.game_list, world.apex_list])

# The mod on, as it is whenever its heirloom is in hand: a choice's change runs only then (mods_base's
# on_change_while_enabled, heirloom_choices.py).
mod.is_enabled = True
axe_skins = {skin["name"]: skin for skin in fake_world.HEIRLOOMS["axe"]["skins"]}
axe_look = axe_skins["own"]["slots"]["Skin"]


def chosen(option, value):
    """A choice as the window saves it: the option set, its change run as mods_base runs it; True, or what it raised."""
    try:
        option.value = value
    except Exception as error:  # a change that raises is a failure of its check, not of the whole test
        return error
    return True


check("the axe chosen: its list given at once in place of the knife's, and said",
      chosen(heirloom_settings.model, "axe") is True and unarmed.AnimSets == [world.game_list, world.axe_list]
      and said("heirloom chosen: axe") and said("our axe apex animations given to empty hands"))
check("its model on the heirloom in hand, in its own look, the game's character material, glowing at force 3",
      mesh.model is world.axe and mesh.names == ["Skin"]
      and mesh.materials[0].parent is world.look[axe_look["parent"]]
      and ("Emissive Intensity (Red Channel)", 2.5) in mesh.materials[0].values
      and said("our axe wears its own skin: 1 of 1 slots dressed"))
check("in its own hold, at the menu's 100 %",
      mesh.fitted_scale == (1.0, -1.0, 1.0) and mesh.fitted_turn == (-2.55, -26.27, -0.53))
check("until the next weapon change the arms play the knife's, and the heirloom hides", not heirloom.playing_ours())
world.rest[0] = "AxeApex"
check("from it they play the axe's, and it shows, drawn and put away with the axe's own",
      heirloom.playing_ours() and heirloom._animation("AS_UA_Equip").split("/")[-2] == "AxeApex")
check("a force chosen: its glow at once", chosen(heirloom_settings.glow, 5) is True
      and ("Emissive Intensity (Red Channel)", 6.4) in mesh.materials[0].values)
kept_dress = heirloom.dress
heirloom.dress = lambda component: (_ for _ in ()).throw(RuntimeError("engine"))
broke = chosen(heirloom_settings.glow, 4)
heirloom.dress = kept_dress
check("a change that fails is written, the choice kept, and the option's next change still runs",
      broke is True and heirloom_settings.glow.value == 4
      and any("glow 4: its change failed" in line for line in state["errors"])
      and chosen(heirloom_settings.glow, 5) is True
      and ("Emissive Intensity (Red Channel)", 6.4) in mesh.materials[0].values)
check("a skin chosen: on it at once, a game material worn as it is", chosen(heirloom_settings.SKINS["axe"], "blood")
      is True and mesh.materials[0].parent is world.look[axe_skins["blood"]["slots"]["Skin"]["parent"]]
      and mesh.model is world.axe)
dressed = len([line for line in state["info"] if " wears its " in line])
check("the knife's skin chosen while the axe is in hand: the axe stays as it is",
      chosen(heirloom_settings.SKINS["jakobs_knife"], "own") is True
      and len([line for line in state["info"] if " wears its " in line]) == dressed
      and mesh.materials[0].parent is world.look[axe_skins["blood"]["slots"]["Skin"]["parent"]])
check("the knife chosen again: its list, its model in its own look, its hold",
      chosen(heirloom_settings.model, "jakobs_knife") is True
      and unarmed.AnimSets == [world.game_list, world.apex_list] and mesh.model is world.knife
      and [copy.parent for copy in mesh.materials] == [world.look[look[slot]["parent"]]
                                                          for slot in ("Base_Mat", "Tech_Mat")]
      and mesh.fitted_scale == (0.62, -0.62, 0.62))
# The inspection, at a press of its key (inspect_keys.py calls heirloom.inspect): the arms play montages from here on.
montages = Arms()
for method in ("PlaySlotAnimationAsDynamicMontage", "Montage_IsPlaying", "Montage_Stop"):
    setattr(world.instance, method, getattr(montages, method))
# Where the parent's tools build the axe's: its lists container, its default mode's folder, beside its draw.
INSPECTION = "/Game/PlayerCharacters/_Shared/Animation/1st/AxeApex/AS_UA_Inspect.AS_UA_Inspect"
inspection = types.SimpleNamespace(Name="AS_UA_Inspect")
rifle = types.SimpleNamespace(Name="OakWeapon_1")


def inspected() -> list[dict]:
    """The inspections played on the arms, in their order: in the draw's slot, by their names."""
    return [played for played in montages.played if played.get("SlotNodeName") == "FullBody"
            and getattr(played.get("Asset"), "Name", "").startswith("AS_UA_Inspect")]


world.rest[0] = "HeirApx"
world.frame()
state["info"].clear()
heirloom.inspect()
check("the knife in the empty hand: it has no inspection, the key plays nothing and says so",
      inspected() == [] and said("the jakobs_knife has no inspection"))
chosen(heirloom_settings.model, "axe")
world.rest[0] = "AxeApex"
world.frame()
state["info"].clear()
heirloom.inspect()
heirloom.inspect()
check("the axe's inspection not in the game yet: said once, nothing played",
      inspected() == [] and len([line for line in state["info"] if "no inspection until" in line]) == 1
      and said("AS_UA_Inspect was not found"))
world.container[INSPECTION] = inspection
heirloom.inspect()
check("in the game since, it waits for the heirloom to be put in a hand again", inspected() == [])
heirloom.show(world.character)
mesh = world.meshes[-1]
heirloom.inspect()
check("put in a hand again, a press plays the axe's own, loaded from its folder, from its start with no fade",
      len(inspected()) == 1 and inspected()[0].get("Asset") is inspection
      and inspected()[0].get("InTimeToStartMontageAt") == 0.0 and inspected()[0].get("BlendInTime") == 0.0
      and package(INSPECTION) in world.loaded)
heirloom.inspect()
again_at = (fake_world.HEIRLOOMS["axe"].get("inspect") or {}).get("again_at")
check("pressed again while it plays: from the first key, fading in briefly",
      again_at is not None and len(inspected()) == 2 and inspected()[1].get("InTimeToStartMontageAt") == again_at
      and inspected()[1].get("BlendInTime") == 0.1)
playing = montages.playing[-1] if montages.playing else None
world.weapon_change(rifle)
check("a weapon drawn while it plays stops it at once", playing is not None and (0.0, playing) in montages.stopped
      and said("inspection stopped"))
heirloom.inspect()
check("a weapon in hand: the key plays nothing", len(inspected()) == 2)
world.weapon_change(None)
heirloom.inspect()
check("the weapon put away again: a press plays it from its start",
      len(inspected()) == 3 and inspected()[2].get("InTimeToStartMontageAt") == 0.0)
playing = montages.playing[-1] if montages.playing else None
eyes = world.camera.GetActorCameraMode
world.camera.GetActorCameraMode = lambda _character: "ThirdPerson"
world.frame()
heirloom.inspect()
check("the camera out of the eyes hides the heirloom: its inspection stops, and the key plays nothing",
      playing is not None and (0.0, playing) in montages.stopped and len(inspected()) == 3)
world.camera.GetActorCameraMode = eyes
world.frame()
CROUCHED = "/Game/PlayerCharacters/_Shared/Animation/1st/AxeApex/AS_UA_Inspect_Crouch.AS_UA_Inspect_Crouch"
world.container[CROUCHED] = types.SimpleNamespace(Name="AS_UA_Inspect_Crouch")
world.character.bIsCrouched = True
heirloom.inspect()
check("the player crouched: a press plays the axe's inspection built on the crouched rest, from its folder",
      len(inspected()) == 4 and inspected()[3].get("Asset") is world.container[CROUCHED]
      and package(CROUCHED) in world.loaded)
world.character.bIsCrouched = False
for method in ("PlaySlotAnimationAsDynamicMontage", "Montage_IsPlaying", "Montage_Stop"):
    delattr(world.instance, method)
chosen(heirloom_settings.model, "jakobs_knife")

chosen(heirloom_settings.glow, 3)
world.rest[0] = "HeirApx"

state["info"].clear()
heirloom.switch_off()
check("switched off: our list taken back, the knife staying while the hands hold it",
      unarmed.AnimSets == [world.game_list] and not mesh.destroyed and mesh.shown is True
      and said("the knife leaves with our animations, at the next weapon change"))
heirloom_choices.mode_chosen("Borderlands")
check("a mode chosen while it leaves gives no list", unarmed.AnimSets == [world.game_list])
heirloom.switch_on()
check("switched on before it left: our list again, and the knife stays",
      unarmed.AnimSets == [world.game_list, world.apex_list] and not heirloom.STATE.retiring and not mesh.destroyed)
heirloom.switch_off()
world.rest[0] = "Unarmed"
world.frame()
check("the game's animations back: the knife leaves the hands and all goes, with the weapon watch",
      mesh.destroyed and said("heirloom off: our knife removed") and not state["raw_hooks"]
      and unarmed.AnimSets == [world.game_list] and heirloom.held() is None)
world.rest[0] = "HeirApx"

# Apex Heirloom switched off while its knife is held, then Heirloom switched on in the same session: Heirloom gives the
# same list, one of the game's objects, before the old knife leaves the hands.
heirloom.show(world.character)
mesh = world.meshes[-1]
heirloom.switch_off()
unarmed.AnimSets.append(world.apex_list)
world.rest[0] = "Unarmed"
world.frame()
check("switched off, another file's list given before its knife leaves: the knife goes, that list stays",
      mesh.destroyed and heirloom.held() is None and unarmed.AnimSets == [world.game_list, world.apex_list])
unarmed.AnimSets.remove(world.apex_list)
world.rest[0] = "HeirApx"

heirloom.show(world.character)
old = world.meshes[-1]
world.character, world.arms, world.instance = world.new_character()
state["pc"].OakCharacter = world.character
check("put on a new character, the old knife leaves the old hands and a new one hangs on the new",
      heirloom.show(world.character) and old.destroyed and not world.meshes[-1].destroyed
      and world.meshes[-1].attached[-1][0] is world.arms and heirloom.holds_for(world.character))
check("... in Wraith's hold again, at the menu's size",
      getattr(world.meshes[-1], "fitted_scale", None) == (0.62, -0.62, 0.62)
      and getattr(world.meshes[-1], "fitted_turn", None) == (-41.1, -44.7, 73.8))

heirloom.switch_off()
heirloom.drop_knife()
world.character, world.arms, world.instance = world.new_character()
state["pc"].OakCharacter = world.character
check("switched off, its knife gone with its character, then put on a new one: it stays, not leaving",
      heirloom.show(world.character) and not heirloom.STATE.retiring)

state["info"].clear()
slots = world.character.ActiveWeapons.Slots
world.character.ActiveWeapons.Slots = []
raised = None
try:
    heirloom.show(world.character)
except Exception as exc:
    raised = exc
check("an error once the knife is hung: raised for the next try, the knife taken away, nothing left on screen",
      isinstance(raised, IndexError) and world.meshes[-1].destroyed and heirloom.held() is None
      and not heirloom.holds_for(world.character) and not state["raw_hooks"])
world.character.ActiveWeapons.Slots = slots

heirloom.remove()
state["info"].clear()
ruins = world.container.pop(look["Base_Mat"]["parent"])
heirloom.show(world.character)
knife = world.meshes[-1]
check("a material of the look the game lacks: its slot keeps the engine's grid, said, the knife hung all the same",
      knife.materials[0] == "grid" and knife.materials[1].parent is world.look[look["Tech_Mat"]["parent"]]
      and knife.attached and said("slot Base_Mat: " + look["Base_Mat"]["parent"] + " not found, left as it is"))
world.container[look["Base_Mat"]["parent"]] = ruins
heirloom.remove()
built = len(world.meshes)

state["info"].clear()
world.loaded.clear()
heirloom_stubs.sdk_stubs.asset_registry(state, lambda _data: (_ for _ in ()).throw(RuntimeError("no such package")))
check("without our list in the game: False, said, nothing built, nothing given",
      not heirloom.show(world.character) and said("our jakobs_knife animations are not in the game")
      and len(world.meshes) == built and unarmed.AnimSets == [world.game_list])
state["info"].clear()
world.loaded.append(package(fake_world.APEX_LIST))
check("without our model: False, said, nothing built, our list taken back",
      not heirloom.show(world.character)
      and said("our jakobs_knife model was not found: is 000_ApexHeirloom_999_P installed?")
      and len(world.meshes) == built and unarmed.AnimSets == [world.game_list])
state["info"].clear()
state["all"]["/Script/Engine.AnimInstance"] = []
check("no arms, no knife", not heirloom.show(world.character) and said("arms were not found"))

definition = definition_fixture.load()
if definition is None:
    definition_fixture.skip("the model loaded is the Jakobs knife's, as its heirloom.json sets it")
else:
    model = definition["model"]
    check("the model loaded is the Jakobs knife's, as its heirloom.json sets it",
          fake_world.HEIRLOOMS["jakobs_knife"]["model"] == f"/Game/ApexHeirloom/{model['name']}.{model['name']}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
